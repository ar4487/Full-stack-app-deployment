// frontend/app.js
const API = window.API_BASE || "http://localhost:8000";

function $(sel){return document.querySelector(sel)}
const authCard = $('#auth'), appCard = $('#app');
const authForm = $('#auth-form'), toggleLink = $('#toggle-link'), authTitle = $('#auth-title'), authBtn = $('#auth-btn'), authMsg = $('#auth-msg');
const noteForm = $('#note-form'), notesList = $('#notes-list');

let isRegister = false;
function setToken(t){ localStorage.setItem('token', t) }
function getToken(){ return localStorage.getItem('token') }
function clearToken(){ localStorage.removeItem('token') }

function showAuth(msg){ authCard.classList.remove('hidden'); appCard.classList.add('hidden'); if(msg) authMsg.textContent = msg; }
function showApp(){ authCard.classList.add('hidden'); appCard.classList.remove('hidden'); authMsg.textContent=''; }

toggleLink.addEventListener('click', (e)=>{
  e.preventDefault();
  isRegister = !isRegister;
  authTitle.textContent = isRegister ? 'Register' : 'Sign in';
  authBtn.textContent = isRegister ? 'Create account' : 'Sign in';
  toggleLink.textContent = isRegister ? 'Sign in' : 'Register';
});

authForm.addEventListener('submit', async (e)=>{
  e.preventDefault();
  const email = $('#email').value;
  const password = $('#password').value;
  try {
    if(isRegister){
      const r = await fetch(`${API}/auth/register`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})});
      if(!r.ok) throw await r.json();
      // auto-login after register
    }
    // login
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    const tokenRes = await fetch(`${API}/auth/token`, {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body: form.toString()});
    if(!tokenRes.ok) throw await tokenRes.json();
    const tokenJson = await tokenRes.json();
    setToken(tokenJson.access_token);
    await loadNotes();
    showApp();
  } catch(err){
    console.error(err);
    authMsg.textContent = (err.detail) ? err.detail : (err.message || JSON.stringify(err));
  }
});

$('#logout').addEventListener('click', ()=>{
  clearToken();
  showAuth();
});

noteForm.addEventListener('submit', async (e)=>{
  e.preventDefault();
  const title = $('#note-title').value.trim();
  const content = $('#note-content').value.trim();
  if(!title) return;
  const token = getToken();
  const r = await fetch(`${API}/notes`, {method:'POST', headers:{'Content-Type':'application/json','Authorization':`Bearer ${token}`}, body: JSON.stringify({title,content})});
  if(r.ok){
    $('#note-title').value='';$('#note-content').value='';
    await loadNotes();
  } else {
    console.error(await r.json());
  }
});

async function loadNotes(){
  const token = getToken();
  if(!token) return showAuth();
  const r = await fetch(`${API}/notes`, {headers:{'Authorization':`Bearer ${token}`}});
  if(r.status === 401 || r.status === 403){ clearToken(); return showAuth() }
  const data = await r.json();
  notesList.innerHTML = '';
  data.forEach(n=>{
    const li = document.createElement('li'); li.className='note';
    li.innerHTML = `<div><h3>${escapeHtml(n.title)}</h3><p>${escapeHtml(n.content||'')}</p></div>
      <div><button data-id="${n.id}" class="del">Delete</button></div>`;
    notesList.appendChild(li);
  });
  document.querySelectorAll('.del').forEach(btn=>{
    btn.addEventListener('click', async (e)=>{
      const id = e.target.dataset.id;
      const rr = await fetch(`${API}/notes/${id}`, {method:'DELETE', headers:{'Authorization':`Bearer ${token}`}});
      if(rr.status===204) loadNotes();
    });
  });
}

function escapeHtml(s){ return String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;') }

(async function init(){
  if(getToken()){
    await loadNotes();
    showApp();
  } else {
    showAuth();
  }
})();
