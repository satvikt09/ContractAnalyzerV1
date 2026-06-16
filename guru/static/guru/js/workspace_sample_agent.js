(function(){
  const chatFeed = document.getElementById('chatFeed');
  const uploadInput = document.getElementById('uploadFiles');
  const uploadForm = document.getElementById('uploadForm');
  const chatForm = document.getElementById('chatForm');
  const jumpToLatest = document.getElementById('jumpToLatest');

  if(!chatFeed) return;

  const AUTOSCROLL_EPSILON = 48;
  let autoScrollEnabled = true;

  function scrollFeed(force){
    if(force){ autoScrollEnabled = true; }
    if(autoScrollEnabled){
      chatFeed.scrollTop = chatFeed.scrollHeight;
    }
  }

  chatFeed.addEventListener('scroll', ()=>{
    const nearBottom = chatFeed.scrollHeight - (chatFeed.scrollTop + chatFeed.clientHeight) <= AUTOSCROLL_EPSILON;
    autoScrollEnabled = nearBottom;
    if(jumpToLatest){
      jumpToLatest.style.display = nearBottom ? 'none' : 'flex';
    }
  });

  if(jumpToLatest){
    jumpToLatest.addEventListener('click', ()=>{
      scrollFeed(true);
      jumpToLatest.style.display = 'none';
    });
  }

  function copyToClipboard(text){
    if(navigator.clipboard && window.isSecureContext){
      return navigator.clipboard.writeText(text);
    }
    return new Promise((resolve, reject)=>{
      try{
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.setAttribute('readonly','');
        ta.style.position = 'absolute';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        const ok = document.execCommand('copy');
        document.body.removeChild(ta);
        ok ? resolve() : reject(new Error('execCommand failed'));
      }catch(err){
        reject(err);
      }
    });
  }

  function bindCopyButtons(){
    chatFeed.querySelectorAll('.chat-action-bar .copy-btn').forEach((btn)=>{
      if(btn.dataset.bound === '1') return;
      btn.dataset.bound = '1';
      btn.addEventListener('click', ()=>{
        const bubble = btn.closest('.chat-entry')?.querySelector('.chat-bubble');
        const text = bubble ? bubble.textContent || '' : '';
        const original = btn.textContent;
        copyToClipboard(text).then(()=>{
          btn.textContent = 'Copied!';
          setTimeout(()=>btn.textContent = original, 1200);
        }).catch(()=>{
          btn.textContent = 'Failed';
          setTimeout(()=>btn.textContent = original, 1200);
        });
      });
    });
  }

  bindCopyButtons();
  scrollFeed(true);

  if(uploadInput && uploadForm){
    uploadInput.addEventListener('change', ()=>{
      uploadForm.submit();
    });
  }

  if(chatForm){
    chatForm.addEventListener('submit', ()=>{
      const loading = document.querySelector('.chat-loading');
      if(loading){ loading.style.display = 'inline-flex'; }
    });
  }

  // TODO: Extend with drag-and-drop if desired. Ensure any fetch/XHR targets https:// in production.
})();
