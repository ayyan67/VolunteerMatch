document.addEventListener('DOMContentLoaded', function () {
    const volunteerList = document.getElementById('volunteer-list');
    const infoContent = document.getElementById('info-content');
    const historyTbody = document.getElementById('history-tbody');
    const user_id = document.getElementById('user-id').textContent;

    let selectedVolunteerElement = null;
    let selectedVolunteer = null;
//    console.log(user_id);
    // Fetch events from the backend
    fetch('/matching/api/events')
        .then(response => response.json())
        .then(data => {
            window.events = data;  
            // After events are fetched, fetch volunteers
//            return fetch('/matching/api/volunteers');
            return fetch('/matching/api/volunteers', {
                    method: 'POST',
                    headers: {
                        'Accept':'application/json',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ user_id })
                })
        })
        .then(response => response.json())
        .then(data => {
            updateVolunteerList(data);
            // Auto-select the first volunteer
            if (data.length > 0) {
                selectVolunteer(volunteerList.firstChild, data[0]);
            }
        })
        .catch(error => console.error('Error fetching data:', error));

    function updateVolunteerList(volunteers) {
        volunteerList.innerHTML = ''; // Clear the list

        for (const volunteer of volunteers) {
            const listItem = document.createElement('li');
            listItem.textContent = `${volunteer.name} - Skills: ${volunteer.skills.join(', ')}`;
            listItem.addEventListener('click', () => selectVolunteer(listItem, volunteer));
            volunteerList.appendChild(listItem);
        }
    }

    function selectVolunteer(listItem, volunteer) {
        if (selectedVolunteerElement) {
            selectedVolunteerElement.classList.remove('selected');
        }
        listItem.classList.add('selected');
        selectedVolunteerElement = listItem;
        selectedVolunteer = volunteer;
        showVolunteerInfo();
        updateVolunteerHistory();
    }

    function showVolunteerInfo() {
        if (selectedVolunteer) {
            infoContent.innerHTML = `
                <p><strong>Name:</strong> ${selectedVolunteer.name}</p>
                <p><strong>Address:</strong> ${selectedVolunteer.address1} ${selectedVolunteer.address2}</p>
                <p><strong>City:</strong> ${selectedVolunteer.city}</p>
                <p><strong>State:</strong> ${selectedVolunteer.state}</p>
                <p><strong>Zip:</strong> ${selectedVolunteer.zip}</p>
                <p><strong>Skills:</strong> ${selectedVolunteer.skills.join(', ')}</p>
                <p><strong>Preferences:</strong> ${selectedVolunteer.preferences}</p>
                <p><strong>Availability:</strong> ${selectedVolunteer.availability.join(', ')}</p>
                <p><strong>Email:</strong> ${selectedVolunteer.email}</p>
            `;
        } else {
            infoContent.innerHTML = '<p>Please select a volunteer.</p>';
        }
    }

    function updateVolunteerHistory() {
        historyTbody.innerHTML = ''; // Clear the table body

        if (selectedVolunteer) {
            // Check if the volunteer has a history property and it's an array
            if (!Array.isArray(selectedVolunteer.history)) {
                console.error('selectedVolunteer.history is not an array:', selectedVolunteer.history);
                return;
            }

            for (const entry of selectedVolunteer.history) {
                const event = window.events.find(event => event.id === entry.event_id);
                if (event) {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${event.name}</td>
                        <td>${event.description}</td>
                        <td>${event.location}</td>
                        <td>${event.required_skills.join(', ')}</td>
                        <td>${event.urgency}</td>
                        <td>${event.date}</td>
                        <td>${entry.status}</td>
                    `;
                    historyTbody.appendChild(row);
                }
            }
        }
    }
});
