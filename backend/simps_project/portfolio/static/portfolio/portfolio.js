let portfolioChart = null; 

document.addEventListener('DOMContentLoaded',()=>
{
    loadPortfolioChart(); 
    const deleteButtons = document.querySelectorAll('.delete_btn');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(){
            const portfolioId = this.getAttribute('data-portfolio-id');
            const url = this.getAttribute('data-url');
            console.log('Portfolio ID:', portfolioId);  
            console.log('Type:', typeof portfolioId);   
            if (!portfolioId) {
                alert('Error: No portfolio ID found!');
                return;
            }
            if(!confirm('Are you sure you want to delete this holding?')){
                return;
            }
            fetch(url,{
                method:'POST',
                headers: {
                    'Content-Type':'application/json',
                    'X-CSRFToken':getCookie('csrftoken')
                }
            })
            .then(response=>{
                console.log('Status:',response.status);
                console.log('Content-Type:',response.headers.get('content-type'));
                return response.text();
            })
            .then(text =>{
                console.log('Response:',text);
                try{
                const data = JSON.parse(text);
                if(data.redirect){
                    window.location.href = data.redirect;
                    return;
                }
                if(data.success){
                    const row = document.getElementById(`holding-${portfolioId}`);
                    const mobileCard = document.getElementById(`holding-mobile-${portfolioId}`);
                    const invest = parseFloat(row.dataset.invest);
                    const current = parseFloat(row.dataset.current);
                    const pl = parseFloat(row.dataset.pl);
                    

                    let totalInvest = parseFloat(document.getElementById('total-invest').dataset.value);
                    let totalCurrent = parseFloat(document.getElementById('total-current').dataset.value);
                    let totalPL = parseFloat(document.getElementById('total-pl').dataset.value);

                    totalInvest-=invest;
                    totalCurrent-= current;
                    totalPL -= pl;
                    let totalPercent = 0;
                    if(totalInvest!= 0){
                        totalPercent = ((totalCurrent-totalInvest)*100)/totalInvest;
                    }
                    
                    const investEl = document.getElementById('total-invest');
                    const currentEl = document.getElementById('total-current');
                    const totalEl = document.getElementById('total-pl');
                    const totalperEl = document.getElementById('total-percent');
                    const plCardEl = document.getElementById('plcard');
                    const percentCardEl =  document.getElementById('percentcard');
                    //Changing colors
                    totalEl.classList.remove('text-green-500', 'text-red-500');
                    totalperEl.classList.remove('text-green-500', 'text-red-500');
                    plCardEl.classList.remove('border-green-500', 'border-red-500');
                    percentCardEl.classList.remove('border-green-500', 'border-red-500');
                    
                    if(totalPL >=0){
                        totalEl.classList.add('text-green-500');
                        plCardEl.classList.add('border-green-500');
                    }
                    else{
                        totalEl.classList.add('text-red-500');
                        plCardEl.classList.add('border-red-500');
                    }

                    if (totalPercent>=0){
                        totalperEl.classList.add('text-green-500');
                        percentCardEl.classList.add('border-green-500');
                    }
                    else{
                        totalperEl.classList.add('text-red-500');
                        percentCardEl.classList.add('border-red-500');
                    }

                    investEl.dataset.value =  totalInvest.toFixed(2);
                    investEl.innerText = '$'+ totalInvest.toFixed(2);
                    currentEl.dataset.value = totalCurrent.toFixed(2);
                    currentEl.innerText = '$'+ totalCurrent.toFixed(2);
                    totalEl.dataset.value = totalPL.toFixed(2);
                    totalEl.innerText = '$'+ totalPL.toFixed(2);
                    totalperEl.dataset.value = totalPercent.toFixed(2);
                    totalperEl.innerText =  totalPercent.toFixed(2) + '%';
                    
                    row.remove();

                    alert('Holding deleted successfully!');
                }
                else{
                    alert('Error: '+data.error);
                }
                loadPortfolioChart();
                }
                catch(e){
                    console.error('Failed to parse JSON:',e);
                    console.error('Response was:',text);
                    alert('Invalid Response from the server');
                }
            })

            .catch(error => {
                console.error('Error:',error);
                alert('Deletion failed. Please try again.');
            });
        });
    });

    document.addEventListener("click",function(e){
        if(e.target.classList.contains('edit_btn')){
            handleEditClick(e.target);
        }
    })

    function handleEditClick(button){
    const row = button.closest('tr');
    const qtycell = row.querySelector('.quantity_cell');

    if(button.classList.contains('editing')){
        save_content(button,row,qtycell);
    }
    else{
        edit_content(button,qtycell);
    }
    }

    function save_content(button,row,qtycell){
        const input = qtycell.querySelector(".qty_input");
        const newQty = parseInt(input.value);
         const cell = button.parentElement;
        const sibling_del = cell.querySelector('.delete_btn');

        if(isNaN(newQty) || newQty <0 ){
            alert("Quantity must be greater than zero.");
            return;
        }

        const symbol = row.dataset.symbol;

        updateQuantity(button,newQty)

        .then(()=>{
            qtycell.innerHTML=newQty;
            button.innerHTML = "Edit";
            button.classList.remove("editing");
            sibling_del.disabled = false;
            sibling_del.style.display = "inline-block";
            recalculatePortfolio();
            loadPortfolioChart();
        })
        .catch(()=>{
            alert("Update failed");
        });
    }

    function edit_content(button,qtycell){
        const current_qty = qtycell.innerText.trim();
        const cell = button.parentElement;
        const sibling_del = cell.querySelector('.delete_btn');
        sibling_del.disabled = true;
        sibling_del.style.display = "none";
        qtycell.innerHTML = `<input type="number" class="qty_input w-16" value="${current_qty}" min="0">`;
        button.innerText="Save";
        button.classList.add("editing");
    }

    function updateQuantity (button,quantity){
        const url = button.getAttribute('data-url');
         
        return fetch(url,{
            method:'POST',
            headers:{
                'Content-Type':'application/json',
                'X-CSRFToken':getCookie('csrftoken')
            },
            body:JSON.stringify({
                quantity: quantity
            })
        })
        
    }

    function recalculatePortfolio(){
        const rows = document.querySelectorAll('tbody tr');
        let totalInvest = 0;
        let totalCurrent = 0;
        rows.forEach(row=>{
            const qtyCell = row.querySelector('.quantity_cell');
            const qtyInput = qtyCell.querySelector('.qty_input');
            const qty = qtyInput ? parseFloat(qtyInput.value) : parseFloat(qtyCell.innerText);

            
            const purchase_price = parseFloat(row.querySelector('.purchase_price').innerText.replace('$',''));
            const current_price = parseFloat(row.querySelector('.current_price').innerText.replace('$',''));

            totalInvest+= qty * purchase_price;
            totalCurrent+= qty * current_price;

        });
        const totalPL = totalCurrent - totalInvest;
        const totalPercent = totalInvest ? (totalPL / totalInvest) * 100 : 0;
        const plCardEl = document.getElementById('plcard');
        const percentCardEl =  document.getElementById('percentcard');
        const investEl = document.getElementById('total-invest');
        const currentEl = document.getElementById('total-current');
        const plEl = document.getElementById('total-pl');
        const percentEl = document.getElementById('total-percent');

        investEl.innerText = '$' + totalInvest.toFixed(2);
        investEl.dataset.value = totalInvest.toFixed(2);
        currentEl.innerText = '$' + totalCurrent.toFixed(2);
        currentEl.dataset.value =  totalCurrent.toFixed(2);
        plEl.innerText = '$' + totalPL.toFixed(2);
        plEl.dataset.value =  totalPL.toFixed(2);
        percentEl.innerText = totalPercent.toFixed(2) + '%';
        percentEl.dataset.value =  totalPercent.toFixed(2);
        
        plCardEl.classList.toggle('border-green-500', totalPL >=0);
        plCardEl.classList.toggle('border-red-500', totalPL <=0);
        percentCardEl.classList.toggle('border-green-500', totalPL >=0);
        percentCardEl.classList.toggle('border-red-500', totalPL <=0);
        
        plEl.classList.toggle('text-green-500', totalPL >= 0);
        plEl.classList.toggle('text-red-500', totalPL < 0);
        percentEl.classList.toggle('text-green-500', totalPL >= 0);
        percentEl.classList.toggle('text-red-500', totalPL < 0);
    }

    function loadPortfolioChart() {
    fetch('/portfolio/chart-data/')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Chart error:', data.error);
                return;
            }
            createPortfolioChart(data);
        })
        .catch(error => {
            console.error('Error loading chart:', error);
        });
    }

    function createPortfolioChart(data) {
    const ctx = document.getElementById('portfolioChart');
    
    if (!ctx) {
        console.error('Chart canvas not found');
        return;
    }
    if (portfolioChart) {
        portfolioChart.destroy();
    }

    portfolioChart = new Chart(ctx.getContext('2d'), {
        type: 'line',
       data: {
    labels: data.dates,
    datasets: [{
        label: 'Portfolio Value',
        data: data.values,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: 'rgb(59, 130, 246)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2
    }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14
                    },
                    bodyFont: {
                        size: 13
                    },
                    callbacks: {
                        label: function(context) {
                            return 'Value: $' + context.parsed.y.toLocaleString(undefined, {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2
                            });
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        },
                        font: {
                            size: 11
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                        drawBorder: false
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 11
                        },
                        maxRotation: 45,
                        minRotation: 0
                    },
                    grid: {
                        display: false
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
    }   
});

function getCookie(name){
    let cookieVal = null;
    if(document.cookie && document.cookie!==''){
        const cookies = document.cookie.split(';');
        for (let i = 0;i<cookies.length;i++){
            const cookie = cookies[i].trim();
            if(cookie.substring(0,name.length +1)=== (name + '=')){
                cookieVal = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieVal;
}

