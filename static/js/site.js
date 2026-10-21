const body = document.body;
const themeToggle = document.getElementById('themeToggle');
function setTheme(theme){body.dataset.theme=theme;localStorage.setItem('gloria-theme',theme);if(themeToggle)themeToggle.textContent=theme==='light'?'☾':'☼';}
setTheme(localStorage.getItem('gloria-theme')||'light');
if(themeToggle)themeToggle.addEventListener('click',()=>setTheme(body.dataset.theme==='dark'?'light':'dark'));

const codeEl=document.getElementById('codeDisplay');
if(codeEl){
 const snippets=[
`from fastapi import FastAPI\nfrom pydantic import BaseModel\nfrom transformers import pipeline\n\napp = FastAPI(title="AI Portfolio")\n\nclass Message(BaseModel):\n    text: str\n\n@app.post("/predict")\nasync def predict(message: Message):\n    result = pipeline("text-generation")\n    return {"status": "ready"}`,
`from flask import Flask, jsonify\nfrom sqlalchemy import create_engine\n\napp = Flask(__name__)\n\n@app.get("/api/projects")\ndef projects():\n    return jsonify({\n        "developer": "Gloria NZIENGI",\n        "stack": ["Python", "Flask", "AI"],\n        "status": "building"\n    })`,
`def prepare_translation(text, model):\n    """Explore NLLB for Lingala text."""\n    tokens = tokenizer(text, return_tensors="pt")\n    output = model.generate(**tokens)\n    translated = tokenizer.decode(\n        output[0], skip_special_tokens=True\n    )\n    return translated`
 ];
 let snippet=0, pos=0, deleting=false;
 function typeCode(){
   const source=snippets[snippet];
   if(!deleting){pos++;if(pos>=source.length){deleting=true;setTimeout(typeCode,2100);return;}}
   else {pos-=3;if(pos<=0){pos=0;deleting=false;snippet=(snippet+1)%snippets.length;}}
   const raw=source.slice(0,pos);
   codeEl.innerHTML=raw.replace(/(&)/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\b(from|import|return|async|def|class|await)\b/g,'<span class="kw">$1</span>')
    .replace(/(".*?"|'.*?')/g,'<span class="str">$1</span>')
    .replace(/\b(FastAPI|Flask|BaseModel|Message|pipeline|predict|projects)\b/g,'<span class="fn">$1</span>');
   codeEl.innerHTML+='<span style="color:#a78bfa">▍</span>';
   setTimeout(typeCode,deleting?18:25);
 }
 typeCode();
}
const chatForm=document.getElementById('chatForm'), chatInput=document.getElementById('chatInput'), chatBody=document.getElementById('chatBody');
function addBubble(text,cls){if(!chatBody)return;const el=document.createElement('div');el.className='bubble '+cls;el.textContent=text;chatBody.appendChild(el);chatBody.scrollTop=chatBody.scrollHeight;}
async function askAssistant(message){
 addBubble(message,'user');
 try{
   const response=await fetch('/assistant',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({message})});
   const data=await response.json();addBubble(data.answer,'bot');
 }catch(e){addBubble('Je peux répondre aux questions sur les projets, les compétences, le parcours et le CV de Gloria.','bot');}
}
if(chatForm)chatForm.addEventListener('submit',e=>{e.preventDefault();const msg=chatInput.value.trim();if(!msg)return;chatInput.value='';askAssistant(msg);});
document.querySelectorAll('[data-question]').forEach(btn=>btn.addEventListener('click',()=>askAssistant(btn.dataset.question)));
const minimize=document.getElementById('chatMinimize');
if(minimize)minimize.addEventListener('click',()=>{const hidden=chatBody.style.display==='none';chatBody.style.display=hidden?'flex':'none';document.querySelector('.chat-form').style.display=hidden?'flex':'none';document.querySelector('.chat-hints').style.display=hidden?'flex':'none';minimize.textContent=hidden?'−':'+';});
const fileInput=document.querySelector('input[name="cv"]'), selected=document.getElementById('selectedFile');
if(fileInput&&selected)fileInput.addEventListener('change',()=>selected.textContent=fileInput.files.length?fileInput.files[0].name:'Aucun fichier sélectionné');
setTimeout(()=>document.querySelectorAll('.flash').forEach(el=>el.remove()),6500);
