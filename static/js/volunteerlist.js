document.addEventListener('DOMContentLoaded', function () {
    const volunteerList = document.getElementById('volunteer-list');
    const infoContent = document.getElementById('info-content');
    const eventList = document.getElementById('event-list');
    const eventContent = document.getElementById('event-content');

    let selectedVolunteerElement = null;
    let selectedVolunteer = null;

    let selectedEventElement = null;
    let selectedEvent = null;
    const user_id = -1;

    // Fetch volunteers from the backend
//    fetch('/matching/api/volunteers')
        fetch('/matching/api/volunteers', {
                method: 'POST',
                headers: {
                    'Accept':'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_id })
        })
        .then(response => response.json())
        .then(data => {
            updateVolunteerList(data);
        })
        .catch(error => console.error('Error fetching volunteers:', error));

    // Fetch events from the backend
    fetch('/matching/api/events')
        .then(response => response.json())
        .then(data => {
            updateEventList(data);
        })
        .catch(error => console.error('Error fetching events:', error));

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
        showInfo();
    }

    function showInfo() {
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
                ${selectedVolunteer.assigned_event ? `<p><strong>Assigned Event:</strong> ${selectedVolunteer.assigned_event}</p>` : `<p><strong>Assigned Event: </strong> None</p>`}
            `;
        } else {
            infoContent.innerHTML = '<p>Please select a volunteer.</p>';
        }
    }

    function updateEventList(events) {
        eventList.innerHTML = ''; // Clear the list

        for (const event of events) {
            const listItem = document.createElement('li');
            listItem.textContent = `${event.name} - ${event.date}`;
            listItem.addEventListener('click', () => selectEvent(listItem, event));
            eventList.appendChild(listItem);
        }
    }

    function selectEvent(listItem, event) {
        if (selectedEventElement) {
            selectedEventElement.classList.remove('selected');
        }
        listItem.classList.add('selected');
        selectedEventElement = listItem;
        selectedEvent = event;
        showEventInfo();
    }

    function showEventInfo() {
        if (selectedEvent) {
            eventContent.innerHTML = `
                <p><strong>Name:</strong> ${selectedEvent.name}</p>
                <p><strong>Description:</strong> ${selectedEvent.description}</p>
                <p><strong>Location:</strong> ${selectedEvent.location}</p>
                <p><strong>Required Skills:</strong> ${selectedEvent.required_skills.join(', ')}</p>
                <p><strong>Urgency:</strong> ${selectedEvent.urgency}</p>
                <p><strong>Date:</strong> ${selectedEvent.date}</p>
            `;
        }
    }

    window.assignEvent = function() {
        if (selectedVolunteer && selectedEvent) {
            fetch('/matching/api/assign_event', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: selectedVolunteer.user_id,
                    volunteer_name: selectedVolunteer.name,
                    event_name: selectedEvent.name
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                    console.log("ERROR");
                } else {
                    alert(data.message);
                    selectedVolunteer.assigned_event = selectedEvent.name;
                    showInfo();
                }
            })
            .catch(error => console.error('Error assigning event:', error));
        } else {
            alert('Please select both a volunteer and an event.');
        }
    }
});
