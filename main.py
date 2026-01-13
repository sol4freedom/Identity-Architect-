import { fetch } from 'wix-fetch';

$w.onReady(function () {
    $w('#generateButton').onClick(async () => {
        
        // UI Reset
        $w('#resultText').text = "Scanning the Cosmos...";
        $w('#resultText').expand();
        
        // 1. Gather Data
        let userTime = $w('#timePicker').value; // e.g., "14:30"
        let userDate = $w('#datePicker').value; 
        let userName = $w('#nameInput').value;
        let struggle = $w('#struggleDropdown').value || "Passion";
        let city = $w('#cityInput').value ? $w('#cityInput').value.formatted : "";

        // 2. Timezone Math (Standard)
        // We calculate the real offset. The new backend will handle decimals perfectly.
        const offsetMinutes = new Date().getTimezoneOffset();
        const tzNumber = -(offsetMinutes / 60); 

        // 3. Send to Server
        try {
            const response = await fetch("https://identity-architect.onrender.com/calculate", {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: userName,
                    date: userDate,   // Backend will fix the format
                    time: userTime,
                    city: city,
                    struggle: struggle,
                    tz: tzNumber      // Backend will fix the decimal
                })
            });

            if (response.ok) {
                const data = await response.json();
                $w('#resultText').text = data.report; 
                $w('#offerButton').expand(); 
            } else {
                const errorMsg = await response.text(); 
                $w('#resultText').text = "Server Error: " + errorMsg;
            }
        } catch (error) {
            console.log(error);
            $w('#resultText').text = "Connection Failed.";
        }
    });
});
