function checkCredentials(event) {
    event.preventDefault(); // Prevent form submission and page reload

    var username = document.querySelector('.input1').value; // Get username value
    var password = document.querySelector('.input2').value; // Get password value

    // Check if the credentials match the defined ones
    if (username === 'cs' && password === 'cs') {
        window.location.href = '../mainpage/cs.html'; // Redirect to cs.html
    } else if (username === 'IT' && password === 'IT') {
        window.location.href = 'it.html'; // Redirect to it.html
    } else if (username === 'bca' && password === 'bca') {
        window.location.href = 'bca.html'; // Redirect to bca.html
    } else {
        alert('Invalid User ID or Password'); // Show error if credentials don't match
    }
}
