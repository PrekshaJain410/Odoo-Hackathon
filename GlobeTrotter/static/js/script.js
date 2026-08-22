document.querySelectorAll('[data-demo]').forEach(button=>{
  button.addEventListener('click',()=>alert(button.dataset.demo));
});