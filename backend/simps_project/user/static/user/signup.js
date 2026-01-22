document.addEventListener('DOMContentLoaded',()=>{
    const error = document.body.dataset.error;
    const form = document.querySelector("form");
    if (error){
        
        alert(error);
    }
})