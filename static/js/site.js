const body = document.body;
const themeToggle = document.getElementById('themeToggle');
function setTheme(theme){body.dataset.theme=theme;localStorage.setItem('gloria-theme',theme);if(themeToggle)themeToggle.textContent=theme==='light'?'☾':'☼';}
setTheme(localStorage.getItem('gloria-theme')||'light');
if(themeToggle)themeToggle.addEventListener('click',()=>setTheme(body.dataset.theme==='dark'?'light':'dark'));

const pageTrack=document.getElementById('pageTrack');
if(pageTrack){
 const pages=Array.from(pageTrack.querySelectorAll('.page-slide'));
 const previousPage=document.getElementById('previousPage');
 const nextPage=document.getElementById('nextPage');
 const pagePosition=document.getElementById('pagePosition');
 const topbar=document.querySelector('.topbar');
 let activePage=0, wheelLockUntil=0;
 const reducedMotion=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 function measureHeader(){if(topbar)document.documentElement.style.setProperty('--header-height',`${topbar.getBoundingClientRect().height}px`);}
 function updatePageControls(){
   if(pagePosition)pagePosition.textContent=`${String(activePage+1).padStart(2,'0')} / ${String(pages.length).padStart(2,'0')}`;
   if(previousPage)previousPage.disabled=activePage===0;
   if(nextPage)nextPage.disabled=activePage===pages.length-1;
 }
 function goToPage(index,target,resetPage=false){
   const nextIndex=Math.max(0,Math.min(pages.length-1,index));
   activePage=nextIndex;
   const slide=pages[activePage];
   pages.forEach((page,pageIndex)=>{
     page.style.transform=`translateX(${(pageIndex-activePage)*100}%)`;
     page.inert=pageIndex!==activePage;
     page.setAttribute('aria-hidden',String(pageIndex!==activePage));
   });
   if(resetPage)slide.scrollTo({top:0,behavior:reducedMotion?'auto':'smooth'});
   if(target&&target!==slide){
     const top=target.getBoundingClientRect().top-slide.getBoundingClientRect().top+slide.scrollTop;
     slide.scrollTo({top,behavior:reducedMotion?'auto':'smooth'});
   }
   updatePageControls();
 }
 pages.forEach((page,index)=>{
   page.style.transform=`translateX(${index*100}%)`;
   page.inert=index!==activePage;
   page.setAttribute('aria-hidden',String(index!==activePage));
 });
 measureHeader();
 window.addEventListener('resize',measureHeader);
 if(previousPage)previousPage.addEventListener('click',()=>goToPage(activePage-1));
 if(nextPage)nextPage.addEventListener('click',()=>goToPage(activePage+1));
 document.querySelectorAll('a[href^="#"]').forEach(link=>link.addEventListener('click',event=>{
   const targetId=link.getAttribute('href').slice(1);
   const target=document.getElementById(targetId);
   const slide=target&&target.closest('.page-slide');
   if(!slide)return;
   event.preventDefault();
   goToPage(pages.indexOf(slide),target,target===slide);
 }));
 window.addEventListener('wheel',event=>{
   const target=event.target;
   if(event.shiftKey||(target instanceof Element&&target.closest('.chat-body')))return;
   const verticalDelta=Math.abs(event.deltaY)>Math.abs(event.deltaX)?event.deltaY:event.deltaX;
   if(Math.abs(verticalDelta)<1)return;
   event.preventDefault();
   if(Date.now()<wheelLockUntil)return;
   goToPage(activePage+(verticalDelta>0?1:-1));
   wheelLockUntil=Date.now()+650;
 },{passive:false});
 pageTrack.addEventListener('keydown',event=>{
   if(event.target.matches('input,textarea,button,[contenteditable="true"]'))return;
   if(event.key==='ArrowRight'){event.preventDefault();goToPage(activePage+1);}
   if(event.key==='ArrowLeft'){event.preventDefault();goToPage(activePage-1);}
 });
 updatePageControls();
}

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
