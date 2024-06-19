const day_select = document.getElementById("day");
const month_select = document.getElementById("month");
const year_select = document.getElementById("year");

const months = ['Janurary', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

(function add_months(){
    for(let i = 0; i < months.length; i++){
        const option = document.createElement('option')
        option.textContent = months[i];
        month_select.appendChild(option);
    };
})