document.addEventListener("submit", (e)=>{
  const btn = e.target.querySelector("button[type=submit].primary")
  if(btn){ btn.dataset.loading = "1"; btn.disabled = true; setTimeout(()=>{btn.disabled=false; btn.dataset.loading="0"}, 800) }
});