const chatbotBtn = document.getElementById('chatbotBtn');
const openChatbotBtn = document.getElementById('openChatbotBtn');
const closeChatbotBtn = document.getElementById('closeChatbotBtn');
const chatbotModal = document.getElementById('chatbotModal');
const appHeader = document.getElementById('appHeader');
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const stopBtn = document.getElementById('stopBtn');
const clearChatBtn = document.getElementById('clearChatBtn');
const aboutBtn = document.getElementById('aboutBtn');
const helpBtn = document.getElementById('helpBtn');
const scrollToTopBtn = document.getElementById('scrollToTopBtn');
const scrollToBottomBtn = document.getElementById('scrollToBottomBtn');

// State variables
let chatHistory = [];
let typingIndicator = null;
let controller = null;
let isGenerating = false;

// Initialize the app
function init() {
  setupEventListeners();
  scrollToBottom();
}

// Set up event listeners
function setupEventListeners() {
  // Chatbot toggle buttons
  chatbotBtn.addEventListener('click', toggleChatbot);
  openChatbotBtn.addEventListener('click', toggleChatbot);
  closeChatbotBtn.addEventListener('click', toggleChatbot);
  
  // Send message on button click or Enter key
  sendBtn.addEventListener('click', sendMessage);
  userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });
  
  // Stop generation button
  stopBtn.addEventListener('click', stopGeneration);
  
  // Clear chat button
  clearChatBtn.addEventListener('click', clearChatHistory);
  
  // About and Help buttons
  aboutBtn.addEventListener('click', () => {
    toggleChatbot();
    setTimeout(() => {
      userInput.value = "Tell me about MSME OSEM";
      sendMessage();
    }, 300);
  });
  
  helpBtn.addEventListener('click', () => {
    toggleChatbot();
    setTimeout(() => {
      userInput.value = "How can you help me with my business?";
      sendMessage();
    }, 300);
  });
  
  // Toggle visibility of "Other" options
  function toggleOtherOptions() {
    const otherOptions = document.getElementById('other-options');
    if (otherOptions) {
      otherOptions.style.display = otherOptions.style.display === 'none' ? 'block' : 'none';
    } else {
      console.error("Element with ID 'other-options' not found.");
    }
  }

  // Quick reply buttons
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('quick-reply-btn')) {
      const btn = e.target;

      // Handle "Find Experts"
      if (btn.id === 'expert-list-btn') {
        showExpertOptions();
        return;
      }
      // Handle "Find Businesses"
      else if (btn.id === 'business-list-btn') {
        showBusinessDistrictSelection();
        return;
      }
      // Handle "Check for CM Loan"
      else if (btn.id === 'checkLoanBtn') {
        startLoanEligibilityCheck();
        return;
      }
      // Handle loan eligibility buttons
      else if (btn.classList.contains('loan-age-btn')) {
        handleLoanAgeSelection(btn.dataset.age);
        return;
      }
      else if (btn.classList.contains('loan-cert-btn')) {
        handleLoanCertSelection(btn.dataset.cert);
        return;
      }

      // Handle "Other" button
      if (btn.textContent.trim().toLowerCase() === 'other') {
        toggleOtherOptions();
        return;
      }

      // For all other buttons
      const replyText = btn.getAttribute('data-reply') || btn.textContent;
      const userInput = document.getElementById('userInput');
      if (userInput) {
        userInput.value = replyText;
        sendMessage();
      } else {
        console.error("Input field with ID 'userInput' not found.");
      }
    }
  });
  
  // Scroll buttons
  scrollToTopBtn.addEventListener('click', () => {
    chatMessages.scrollTop = 0;
    scrollToTopBtn.classList.add('active');
    setTimeout(() => scrollToTopBtn.classList.remove('active'), 500);
  });
  
  scrollToBottomBtn.addEventListener('click', scrollToBottom);
  
  // Auto-show/hide scroll buttons based on scroll position
  chatMessages.addEventListener('scroll', () => {
    // Show scroll-to-bottom button if not at bottom
    if (chatMessages.scrollHeight - chatMessages.scrollTop - chatMessages.clientHeight > 50) {
      scrollToBottomBtn.style.display = 'flex';
    } else {
      scrollToBottomBtn.style.display = 'flex';
    }
    
    // Show scroll-to-top button if scrolled down
    if (chatMessages.scrollTop > 50) {
      scrollToTopBtn.style.display = 'flex';
    } else {
      scrollToTopBtn.style.display = 'flex';
    }
  });
}

// Toggle chatbot visibility
function toggleChatbot() {
  chatbotModal.classList.toggle('active');
  appHeader.classList.toggle('hidden');
  chatbotBtn.classList.toggle('hidden');
  
  if (chatbotModal.classList.contains('active')) {
    userInput.focus();
    // Show both scroll buttons initially
    scrollToTopBtn.style.display = 'flex';
    scrollToBottomBtn.style.display = 'flex';
  }
}

// Display a message in the chat
function displayMessage(sender, content) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message message-${sender}`;
  
  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.textContent = sender === 'user' ? 'Y' : 'O';
  
  const messageContent = document.createElement('div');
  messageContent.className = 'message-content';
  messageContent.innerHTML = content;
  
  messageDiv.appendChild(avatar);
  messageDiv.appendChild(messageContent);
  
  chatMessages.appendChild(messageDiv);
  scrollToBottom();
  
  // Add to chat history
  chatHistory.push({
    sender,
    content,
    timestamp: new Date().toISOString()
  });
}

// Show typing indicator
function showTypingIndicator() {
  if (!typingIndicator) {
    typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator';
    typingIndicator.innerHTML = '<span></span><span></span><span></span>';
    chatMessages.appendChild(typingIndicator);
    scrollToBottom();
  }
}

// Remove typing indicator
function removeTypingIndicator() {
  if (typingIndicator) {
    typingIndicator.remove();
    typingIndicator = null;
  }
}

// Scroll to bottom of chat
function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
  // Add animation effect to scroll-to-bottom button
  scrollToBottomBtn.classList.add('active');
  setTimeout(() => scrollToBottomBtn.classList.remove('active'), 500);
}

// Stop response generation
function stopGeneration() {
  if (controller) {
    controller.abort();
    isGenerating = false;
    stopBtn.style.display = 'none';
    sendBtn.style.display = 'flex';
    removeTypingIndicator();
    displayMessage('bot', 'Response generation stopped.');
    enableInput();
  }
}

// Enable input field and buttons
function enableInput() {
  userInput.disabled = false;
  sendBtn.disabled = false;
}

// Disable input field and buttons
function disableInput() {
  userInput.disabled = true;
  sendBtn.disabled = true;
}

// Send message to backend
async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;
  
  // Display user message
  displayMessage('user', message);
  userInput.value = '';
  
  // Disable input during processing
  disableInput();
  showTypingIndicator();
  
  // Show stop button
  stopBtn.style.display = 'flex';
  sendBtn.style.display = 'none';
  isGenerating = true;
  
  // Create AbortController for the request
  controller = new AbortController();
  
  try {
    // Call the actual backend API
    const response = await fetch('/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
      signal: controller.signal
    });

    // Check if the response is successful
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Process the streamed response
    await processStreamedResponse(response);
    
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('Request aborted by user');
    } else {
      console.error('Error:', error);
      removeTypingIndicator();
      displayMessage('bot', 'Sorry, something went wrong. Please try again later.');
    }
  } finally {
    // Reset UI state
    stopBtn.style.display = 'none';
    sendBtn.style.display = 'flex';
    isGenerating = false;
    enableInput();
    userInput.focus();
  }
}

// Show expert options
function showExpertOptions() {
  const messageDiv = document.createElement('div');
  messageDiv.className = 'message message-bot';
  messageDiv.innerHTML = `
    <div class="message-avatar">O</div>
    <div class="message-content">
      <p>How would you like to find experts?</p>
      <div class="expert-options" style="display: flex; gap: 12px; margin-top: 12px; flex-wrap: wrap;">
        <button id="byDistrictBtn" style="
          padding: 10px 16px;
          background-color: var(--primary-color);
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
          display: flex;
          align-items: center;
          gap: 8px;
          transition: background-color 0.3s ease;
        ">
          <i class="fas fa-map-marker-alt"></i> By District
        </button>
        <button id="byDesignationBtn" style="
          padding: 10px 16px;
          background-color: var(--primary-dark);
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
          display: flex;
          align-items: center;
          gap: 8px;
          transition: background-color 0.3s ease;
        ">
          <i class="fas fa-user-tag"></i> By Expertise
        </button>
      </div>
    </div>
  `;
  chatMessages.appendChild(messageDiv);
  scrollToBottom();
  
  // Add event listeners to option buttons
  document.getElementById('byDistrictBtn').addEventListener('click', showDistrictSelection);
  document.getElementById('byDesignationBtn').addEventListener('click', showDesignationSelection);
}

// Show district selection for experts
function showDistrictSelection() {
  // Show loading indicator
  const loadingIndicator = document.createElement('div');
  loadingIndicator.className = 'message message-bot';
  loadingIndicator.innerHTML = `
    <div class="message-avatar">O</div>
    <div class="message-content">Fetching districts...</div>
  `;
  chatMessages.appendChild(loadingIndicator);
  scrollToBottom();

  fetch('/api/expert_list')
    .then(response => response.json())
    .then(data => {
      // Remove loading indicator
      chatMessages.removeChild(loadingIndicator);
      
      if (data.districts && data.districts.length > 0) {
        const districtOptions = data.districts.map(district => 
          `<button class="district-option" data-district="${district}">${district}</button>`
        ).join('');

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message message-bot';
        messageDiv.innerHTML = `
          <div class="message-avatar">O</div>
          <div class="message-content">
            <p>Please select a district:</p>
            <div class="district-options">${districtOptions}</div>
          </div>
        `;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
        
        // Add event listeners to district buttons
        document.querySelectorAll('.district-option').forEach(button => {
          button.addEventListener('click', () => {
            const district = button.getAttribute('data-district');
            fetchExpertsForDistrict(district);
          });
        });
      } else {
        displayMessage('bot', 'No districts with experts found.');
      }
    })
    .catch(error => {
      console.error('Error fetching districts:', error);
      chatMessages.removeChild(loadingIndicator);
      displayMessage('bot', 'Sorry, I couldn\'t fetch the districts. Please try again later.');
    });
}

// Show designation selection for experts
function showDesignationSelection() {
  // Show loading indicator
  const loadingIndicator = document.createElement('div');
  loadingIndicator.className = 'message message-bot';
  loadingIndicator.innerHTML = `
    <div class="message-avatar">O</div>
    <div class="message-content">Fetching expertise areas...</div>
  `;
  chatMessages.appendChild(loadingIndicator);
  scrollToBottom();
  
  // Fetch designations from backend API
  fetch('/api/expert_designations')
    .then(response => response.json())
    .then(data => {
      // Remove loading indicator
      chatMessages.removeChild(loadingIndicator);
      
      if (data.designations && data.designations.length > 0) {
        const designationOptions = data.designations.map(designation => 
          `<button class="district-option" data-designation="${designation}">${designation}</button>`
        ).join('');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message message-bot';
        messageDiv.innerHTML = `
          <div class="message-avatar">O</div>
          <div class="message-content">
            <p>Please select an expertise area:</p>
            <div class="district-options">${designationOptions}</div>
          </div>
        `;
        chatMessages.appendChild(messageDiv);
        scrollToBottom(); 

        // Add event listeners to designation buttons
        document.querySelectorAll('.district-option').forEach(button => {
          button.addEventListener('click', () => {
            const designation = button.getAttribute('data-designation');
            fetchExpertsByDesignation(designation);
          });
        });
      } else {
        displayMessage('bot', 'No expertise areas found.');
      }
    })
    .catch(error => {
      console.error('Error fetching designations:', error);
      chatMessages.removeChild(loadingIndicator);
      displayMessage('bot', 'Sorry, I couldn\'t fetch the expertise areas. Please try again later.');
    });
}


// Fetch experts for a district
function fetchExpertsForDistrict(district) {
  // Show loading indicator
  const loadingIndicator = document.createElement('div');
  loadingIndicator.className = 'message message-bot';
  loadingIndicator.innerHTML = `
    <div class="message-avatar">O</div>
    <div class="message-content">Finding experts in ${district}...</div>
  `;
  chatMessages.appendChild(loadingIndicator);
  scrollToBottom();

  // Fetch experts from backend
  fetch(`/api/experts_in_district?district=${encodeURIComponent(district)}`)
    .then(response => response.json())
    .then(data => {
      // Remove loading indicator
      chatMessages.removeChild(loadingIndicator);
      
      if (data.experts && data.experts.length > 0) {
        const expertsList = data.experts.map(expert => `
          <div class="expert-card">
            <strong>${expert.name}</strong>
            <div><span class="expert-label">Designation:</span> ${expert.designation}</div>
            <div><span class="expert-label">Email:</span> ${expert.email}</div>
            <div><span class="expert-label">Phone:</span> ${expert.mobile}</div>
            <div class="expert-district">${district}</div>
          </div>
        `).join('');
     


    const messageDiv = document.createElement('div');
        messageDiv.className = 'message message-bot';
        messageDiv.innerHTML = `
          <div class="message-avatar">O</div>
          <div class="message-content">
            <p>Experts in ${district}:</p>
            <div class="experts-list">${expertsList}</div>
          </div>
        `;
        chatMessages.appendChild(messageDiv);
      } else {
        displayMessage('bot', `No experts found in ${district}.`);
      }
    })
    .catch(error => {
      console.error('Error fetching experts:', error);
      chatMessages.removeChild(loadingIndicator);
      displayMessage('bot', 'Sorry, I couldn\'t fetch the experts. Please try again later.');
    });
}

 // Fetch experts by designation
function fetchExpertsByDesignation(designation) {
  // Show loading indicator
  const loadingIndicator = document.createElement('div');
  loadingIndicator.className = 'message message-bot';
  loadingIndicator.innerHTML = `
    <div class="message-avatar">O</div>
    <div class="message-content">Finding ${designation} experts...</div>
  `;
  chatMessages.appendChild(loadingIndicator);
  scrollToBottom();
  
  // Fetch experts from backend API
  fetch(`/api/experts_by_designation?designation=${encodeURIComponent(designation)}`)
    .then(response => response.json())
    .then(data => {
      // Remove loading indicator
      chatMessages.removeChild(loadingIndicator);
      
      if (data.experts && data.experts.length > 0) {
        const expertsList = data.experts.map(expert => `
          <div class="expert-card">
            <strong>${expert.name}</strong>
            <div><span class="expert-label">Designation:</span> ${designation}</div>
            <div><span class="expert-label">District:</span> ${expert.district}</div>
            <div><span class="expert-label">Email:</span> ${expert.email}</div>
            <div><span class="expert-label">Phone:</span> ${expert.mobile}</div>
          </div>
        `).join('');
        

   const messageDiv = document.createElement('div');
        messageDiv.className = 'message message-bot';
        messageDiv.innerHTML = `
          <div class="message-avatar">O</div>
          <div class="message-content">
            <p>${designation} experts:</p>
            <div class="experts-list">${expertsList}</div>
          </div>
        `;
        chatMessages.appendChild(messageDiv);
      } else {
        displayMessage('bot', `No ${designation} experts found.`);
      }
    })
    .catch(error => {
      console.error('Error fetching experts:', error);
      chatMessages.removeChild(loadingIndicator);
      displayMessage('bot', 'Sorry, I couldn\'t fetch the experts. Please try again later.');
    });
}


// Show district selection for businesses
function showBusinessDistrictSelection() {
  // Show loading indicator
  const loadingIndicator = document.createElement('div');
  loadingIndicator.className = 'message message-bot';
  loadingIndicator.innerHTML = `
    <div class="message-avatar">O</div>
    <div class="message-content">Fetching business districts...</div>
  `;
  chatMessages.appendChild(loadingIndicator);
  scrollToBottom();

  // Fetch districts from business API
  fetch('/api/business_list')
    .then(response => {
      if (!response.ok) {
        throw new Error('Failed to fetch districts');
      }
      return response.json();
    })
    .then(data => {
      chatMessages.removeChild(loadingIndicator);

      if (data.districts && data.districts.length > 0) {
        const districtOptions = data.districts.map(district =>
          `<button class="district-option" data-district="${district}">${district}</button>`
        ).join('');

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message message-bot';
        messageDiv.innerHTML = `
          <div class="message-avatar">O</div>
          <div class="message-content">
            <p>Please select a district to find businesses:</p>
            <div class="district-options">${districtOptions}</div>
          </div>
        `;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();


    // Add event listeners to district buttons
        document.querySelectorAll('.district-option').forEach(button => {
          button.addEventListener('click', () => {
            const district = button.getAttribute('data-district');
            fetchBusinessesByDistrict(district);
          });
        });
      } else {
        displayMessage('bot', 'No districts with businesses found.');
      
      }
    })
    .catch(error => {
      console.error('Error fetching business districts:', error);
      chatMessages.removeChild(loadingIndicator);
      displayMessage('bot', 'Sorry, I couldn\'t fetch business districts. Please try again later.');
    });
}

// Fetch businesses by selected district
function fetchBusinessesByDistrict(district) {
  const encodedDistrict = encodeURIComponent(district);

  // Show loading indicator
  const loadingIndicator = document.createElement('div');
  loadingIndicator.className = 'message message-bot';
  loadingIndicator.innerHTML = `
    <div class="message-avatar">O</div>
    <div class="message-content">Loading businesses in ${district}...</div>
  `;
  chatMessages.appendChild(loadingIndicator);
  scrollToBottom();

  fetch(`/api/business_in_district?district=${encodedDistrict}`)
    .then(response => {
      if (!response.ok) {
        throw new Error('Failed to fetch businesses');
      }
      return response.json();
    })
    .then(data => {
      chatMessages.removeChild(loadingIndicator);

      const businesses = data.business || [];

      if (businesses.length > 0) {
        const businessesList = businesses.map(business => `
          <div class="business-card">
            <strong>${business.name}</strong>
            <div><span class="business-label">Email:</span> ${business.email}</div>
            <div><span class="business-label">Phone:</span> ${business.mobile}</div>
            <div class="business-district"><span class="business-label">District:</span> ${district}</div>
          </div>
        `).join('');

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message message-bot';
        messageDiv.innerHTML = `
          <div class="message-avatar">O</div>
          <div class="message-content">
            <p>Businesses available in ${district}:</p>
            <div class="businesses-list">${businessesList}</div>
          </div>
        `;
        chatMessages.appendChild(messageDiv);
      } else {
        displayMessage('bot', `No businesses found in ${district}.`);
      }
    })
    .catch(error => {
      console.error('Error fetching businesses:', error);
      chatMessages.removeChild(loadingIndicator);
      displayMessage('bot', 'Sorry, I couldn\'t fetch businesses. Please try again later.');
    });
}

// Process streamed response from backend
async function processStreamedResponse(response) {
  removeTypingIndicator();
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let botMessage = '';
  
  // Create message container for bot response
  const messageDiv = document.createElement('div');
  messageDiv.className = 'message message-bot';
  
  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.textContent = 'O';
  
  const messageContent = document.createElement('div');
  messageContent.className = 'message-content';
  
  messageDiv.appendChild(avatar);
  messageDiv.appendChild(messageContent);
  chatMessages.appendChild(messageDiv);
  
  // Read the stream
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    botMessage += chunk;
    messageContent.innerHTML = botMessage;
    scrollToBottom();
  }
}

// Start loan eligibility check
function startLoanEligibilityCheck() {
  displayMessage('user', 'I want to check for CM Loan eligibility.');
  
  const botMessage = document.createElement('div');
  botMessage.className = 'message message-bot';
  botMessage.innerHTML = `
    <div class="message-avatar">O</div>
    <div class="message-content">
      <p>Please select your age range:</p>
      <div class="quick-replies" style="margin-top: 12px;">
        <button class="quick-reply-btn loan-age-btn" data-age="0-20">0-20</button>
        <button class="quick-reply-btn loan-age-btn" data-age="21-40">21-40</button>
      </div>
    </div>
  `;
  chatMessages.appendChild(botMessage);
  scrollToBottom();
}

// Handle age selection in loan flow
function handleLoanAgeSelection(age) {
  displayMessage('user', age);
  
  if (age === '0-20') {
    displayMessage('bot', ' Sorry, minimum age for loan is 21.');
  } else if (age === '21-40') {
    const botMessage = document.createElement('div');
    botMessage.className = 'message message-bot';
    botMessage.innerHTML = `
      <div class="message-avatar">O</div>
      <div class="message-content">
        <p>Do you have a skill/training certificate?</p>
        <div class="quick-replies" style="margin-top: 12px;">
          <button class="quick-reply-btn loan-cert-btn" data-cert="yes">Yes</button>
          <button class="quick-reply-btn loan-cert-btn" data-cert="no">No</button>
        </div>
      </div>
    `;
    chatMessages.appendChild(botMessage);
    scrollToBottom();
  }
}

// Handle certificate selection in loan flow
function handleLoanCertSelection(cert) {
  displayMessage('user', cert === 'yes' ? 'Yes' : 'No');

  if (cert === 'no') {
    displayMessage(
      'bot',
      'Sorry, you are not eligible.<br>Visit <a href="https://udyami.upicon.in/" target="_blank">UPICON e-Learnings</a> to take certification.'
    );
  } else if (cert === 'yes') {
    displayMessage(
  'bot',
  'You are eligible for the loan.<br>Please contact my team for more information and guidance on the next steps.<br>You can reach us via phone, email, or visit our office during working hours.'
);
  }
}
// Clear chat history
async function clearChatHistory() {
  if (confirm('Are you sure you want to clear the chat history?')) {
    try {
      // Call the backend API to clear chat history
      const response = await fetch('/api/clear_chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error('Failed to clear chat history');
      }

      // Reset the chat UI
      chatMessages.innerHTML = `
        <div class="message message-bot">
          <div class="message-avatar">O</div>
          <div class="message-content">
            <p>Hello! I'm your MSME OSEM Assistant. How can I help you today?</p>
            <div class="quick-replies">
              <button class="quick-reply-btn" data-reply="Tell me about CMYUVA scheme">CMYUVA Scheme</button>
              <button class="quick-reply-btn" data-reply="What is UPICON?">UPICON</button>
              <button class="quick-reply-btn" data-reply="How to register my MSME?">MSME Registration</button>
              <button class="quick-reply-btn" data-reply="What is Youth Adda">Youth Adda</button>
              <button class="quick-reply-btn" id="expert-list-btn">Find Experts</button>
              <button class="quick-reply-btn" id="business-list-btn">Find Businesses</button>
              <button class="quick-reply-btn" id="checkLoanBtn">Check for CM Loan</button>
            </div>
          </div>
        </div>
      `;
      chatHistory = [];
    } catch (error) {
      console.error('Error clearing chat history:', error);
      alert('Failed to clear chat history. Please try again.');
    }
  }
}

document.addEventListener('DOMContentLoaded', init);