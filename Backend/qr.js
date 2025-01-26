let caption = document.querySelector(".caption");
let qr_text = document.querySelector("#email");
let btnGenerate = document.querySelector(".btnGenerate");
let qr_code_output = document.querySelector(".qr_code_output");

btnGenerate.addEventListener("click", () => {
    let text = qr_text.value.trim();
    if (text === "") {
        qr_code_output.style.display = "none";
        caption.innerHTML = "Please enter text to generate a QR code.";
        caption.style.color = "red";
    } else {
        qr_code_output.innerHTML = ""; // Clear previous QR code
        qr_code_output.style.display = "block";
        caption.style.color = "purple";
        caption.innerHTML = "QR Code Generated";

        // Generate QR Code
        new QRCode(qr_code_output, {
            text: text,
            width: 380,
            height: 360,
            colorDark: "#000000",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H,
        });
    }
});
