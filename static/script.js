let selectedPackage = {};

const selectPackage = (packageName, packageAmount) => {
    document.getElementById("payment-modal").style.display = "flex";
    console.log(`You selected: ${packageName} @ Ksh ${packageAmount}`);
    selectedPackage = {packageName, packageAmount};
    
}

const closeModal = (modalId) => {
    document.getElementById(modalId).style.display = "none";
}


const showProcessingModel = () => {
    const processingModel = document.getElementById("processing-modal");
    processingModel.style.display = "flex";
    setTimeout(()=>{
        processingModel.style.display = "none";
        // const successModal = document.getElementById("success-modal");
        // successModal.style.display = "flex";
        // setTimeout(()=> closeModal('success-modal'), 5000);
    }, 2000);

}


const initiatePayment = (event) => {
    event.preventDefault();

    const phoneNumber = document.getElementById('phone-number').value.trim();

    if (!phoneNumber){
        alert("Please enter your phone number to initiate Mpesa payment");
        return;
    }


    const paymentData = {
        ...selectedPackage, phoneNumber
    };

    console.log("Payment details are: ", paymentData);


    // send the data to the server
    fetch('/process-payment', {
        method : 'POST',
        headers: {
            'Content-Type' : 'application/json',
        },
        body: JSON.stringify(paymentData),
    })
    .then(response => response.json())
    .then(data => {
        console.log("This is data to the server: ", data);
    })
    .catch(error => {
        console.error("Error: ", error);
    });

    closeModal('payment-modal');
    showProcessingModel();

    const urlParams = new URLSearchParams(window.location.search);
    const mac = urlParams.get('mac');
    console.log("MAC Address: ", mac);
    document.getElementById('mac').value = mac;
}
document.getElementById('payment-form').addEventListener('submit', initiatePayment);






    


    
    
    
    
    









