"""Pre-registered local coordinator experiment (no production model changes)."""
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parent
os.environ['HF_HUB_OFFLINE']='1'
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
os.environ['TOKENIZERS_PARALLELISM']='false'
os.environ['HF_HOME']=str(ROOT/'cache')
os.environ['TORCH_HOME']=str(ROOT/'cache'/'torch')
import argparse,contextlib,gc,hashlib,json,random,time
import numpy as np
import torch
from transformers import AutoModelForCausalLM,AutoTokenizer,BitsAndBytesConfig,set_seed
from peft import LoraConfig,get_peft_model,prepare_model_for_kbit_training,PeftModel
from benchmark import messages,grade

def read(split):return [json.loads(l) for l in (ROOT/f'{split}.jsonl').read_text(encoding='utf8').splitlines()]
def write(name,data):(ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
def log(msg):print(json.dumps(msg,ensure_ascii=False),flush=True)
def load():
    set_seed(4101);torch.set_num_threads(8)
    tokenizer=AutoTokenizer.from_pretrained(ROOT/'base',local_files_only=True)
    tokenizer.pad_token=tokenizer.eos_token;tokenizer.padding_side='left'
    model=AutoModelForCausalLM.from_pretrained(ROOT/'base',local_files_only=True,quantization_config=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.bfloat16),torch_dtype=torch.bfloat16,device_map={'':0},attn_implementation='sdpa')
    return model,tokenizer

def tokenized(tokenizer,case,answer=False):
    prompt=tokenizer.apply_chat_template(messages(case),tokenize=False,add_generation_prompt=True,enable_thinking=False)
    ids=tokenizer(prompt,add_special_tokens=False)['input_ids']
    if not answer:return ids
    completion=tokenizer(json.dumps(case['target'],ensure_ascii=False,separators=(',',':'))+tokenizer.eos_token,add_special_tokens=False)['input_ids']
    if len(ids)+len(completion)>1536:raise ValueError('Example exceeds frozen context limit; do not silently truncate')
    return ids+completion,len(completion)

def loss_for(model,encoded):
    ids,n=encoded;inputs=torch.tensor([ids],device='cuda')
    # Compute loss only on assistant completion; source/prompt tokens are never training targets.
    logits=model(input_ids=inputs,use_cache=False,logits_to_keep=n+1).logits[:,:-1,:]
    return torch.nn.functional.cross_entropy(logits.reshape(-1,logits.shape[-1]).float(),inputs[:,-n:].reshape(-1))

def evaluate(model,tokenizer,cases,label):
    model.eval();model.gradient_checkpointing_disable();model.config.use_cache=True
    results=[];began=time.monotonic();batch_size=4
    for start in range(0,len(cases),batch_size):
        batch=cases[start:start+batch_size]
        texts=[tokenizer.apply_chat_template(messages(c),tokenize=False,add_generation_prompt=True,enable_thinking=False) for c in batch]
        inputs=tokenizer(texts,return_tensors='pt',padding=True,add_special_tokens=False).to('cuda')
        torch.cuda.synchronize();t=time.monotonic()
        with torch.inference_mode():generated=model.generate(**inputs,max_new_tokens=128,do_sample=False,use_cache=True,pad_token_id=tokenizer.pad_token_id,eos_token_id=tokenizer.eos_token_id)
        torch.cuda.synchronize();elapsed=time.monotonic()-t
        outputs=tokenizer.batch_decode(generated[:,inputs['input_ids'].shape[1]:],skip_special_tokens=True)
        for c,output in zip(batch,outputs):results.append({'id':c['id'],'kind':c['kind'],'language':c['language'],'output':output,'metrics':grade(output.strip(),c),'batch_seconds':elapsed,'batch_size':len(batch)})
        log({'evaluation':label,'done':len(results),'total':len(cases)})
    write(f'{label}_predictions.json',results)
    summary={'label':label,'count':len(results),'seconds':round(time.monotonic()-began,2),'metrics':{key:sum(r['metrics'][key] for r in results) for key in ['valid','routing_correct','disposition_correct','pass','premature_finalization']},'peak_gpu_allocated_gib':round(torch.cuda.max_memory_allocated()/2**30,3)}
    write(f'{label}_summary.json',summary);log(summary);return summary

def run():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');parser.add_argument('--evaluate-only',action='store_true');args=parser.parse_args()
    started=time.monotonic();model,tokenizer=load();log({'loaded':True,'gpu':torch.cuda.get_device_name(0),'allocated_gib':torch.cuda.memory_allocated()/2**30})
    if args.evaluate_only:
        evaluate(model,tokenizer,read('test'),'pretrained_nf4')
        model=PeftModel.from_pretrained(model,ROOT/'checkpoints'/'selected',is_trainable=False)
        evaluate(model,tokenizer,read('test'),'finetuned_nf4');return
    train=[tokenized(tokenizer,c,True) for c in read('train')];val=[tokenized(tokenizer,c,True) for c in read('validation')]
    write('token_lengths.json',{'train_max':max(len(x[0]) for x in train),'train_mean':sum(len(x[0]) for x in train)/len(train),'validation_max':max(len(x[0]) for x in val)})
    model=prepare_model_for_kbit_training(model,use_gradient_checkpointing=True,gradient_checkpointing_kwargs={'use_reentrant':False})
    # Frozen embedding/output layers need not be stored in float32 on this 16GB card.
    model.get_input_embeddings().to(torch.bfloat16);model.get_output_embeddings().to(torch.bfloat16)
    # prepare_model_for_kbit_training upcasts the final norm to float32; cast lm_head's input to match its bfloat16 weight.
    model.get_output_embeddings().register_forward_pre_hook(lambda module,args:(args[0].to(module.weight.dtype),)+tuple(args[1:]))
    config=LoraConfig(r=8,lora_alpha=16,lora_dropout=0.05,target_modules=['q_proj','k_proj','v_proj','o_proj'],bias='none',task_type='CAUSAL_LM')
    model=get_peft_model(model,config);model.config.use_cache=False
    parameters=[p for p in model.parameters() if p.requires_grad]
    log({'trainable_parameters':sum(p.numel() for p in parameters),'total_parameters':sum(p.numel() for p in model.parameters())})
    optimizer=torch.optim.AdamW(parameters,lr=1e-4,weight_decay=0.01)
    model.train();torch.cuda.reset_peak_memory_stats();optimizer.zero_grad(set_to_none=True)
    if args.smoke:
        loss=loss_for(model,train[0]);loss.backward();optimizer.step();torch.cuda.synchronize();log({'smoke_loss':float(loss.detach()),'peak_gib':torch.cuda.max_memory_allocated()/2**30,'elapsed':time.monotonic()-started});return
    epochs=2;accum=8;total_steps=epochs*len(train)//accum;step=0;history=[];best=float('inf');chosen=None;train_started=time.monotonic()
    for epoch in range(epochs):
        order=list(range(len(train)));random.Random(4101+epoch).shuffle(order);running=0
        model.train();model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
        for number,i in enumerate(order):
            loss=loss_for(model,train[i]);(loss/accum).backward();running+=float(loss.detach())
            if (number+1)%accum==0:
                torch.nn.utils.clip_grad_norm_(parameters,1.0);step+=1
                scale=min(1.0,step/6)*max(0.1,(total_steps-step+1)/max(1,total_steps-6))
                for group in optimizer.param_groups:group['lr']=1e-4*scale
                optimizer.step();optimizer.zero_grad(set_to_none=True)
                record={'epoch':epoch+1,'step':step,'loss':round(running/accum,6),'elapsed_seconds':round(time.monotonic()-train_started,2),'gpu_allocated_gib':round(torch.cuda.memory_allocated()/2**30,3)};history.append(record);log(record);running=0;write('training_history.json',history)
        model.eval();losses=[]
        with torch.no_grad():
            for v in val:losses.append(float(loss_for(model,v)))
        average=sum(losses)/len(losses);log({'epoch':epoch+1,'validation_loss':average})
        model.save_pretrained(ROOT/'checkpoints'/f'epoch-{epoch+1}',safe_serialization=True)
        if average<best:
            best=average;chosen=epoch+1;model.save_pretrained(ROOT/'checkpoints'/'selected',safe_serialization=True)
        write('training_result.json',{'epochs_completed':epoch+1,'selected_epoch':chosen,'validation_loss':best,'training_seconds':round(time.monotonic()-train_started,2),'peak_gpu_allocated_gib':round(torch.cuda.max_memory_allocated()/2**30,3),'train_examples':len(train),'validation_examples':len(val),'optimizer_steps':step,'seed':4101,'learning_rate':1e-4,'lora_rank':8,'lora_alpha':16,'targets':['q_proj','k_proj','v_proj','o_proj'],'trainable_parameters':sum(p.numel() for p in parameters)})
    tokenizer.save_pretrained(ROOT/'checkpoints'/'selected');log({'training_complete':True,'selected_epoch':chosen})
    # Separate fresh load is used for matched evaluation, to keep inference dtypes identical.

if __name__=='__main__':run()
