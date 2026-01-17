let content = document.querySelector(".content-area")


for(let i = 1; i<100;i++)
{
    setTimeout(() => {
        content.style.opacity = i+"%"
    }, (i*i)/(8));
    
}


function formatDate(raw) {
    const date = new Date(raw.replace(" ", "T"));

    const options = {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
    };

    return date.toLocaleString("pl-PL", options);
}

function destroy(event)
{
    event.target.remove()
}