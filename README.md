# Multi User LLM SMS Assistant with Realtime Data Aquisition 
The SMS LLM assistant is a powerful Flask web application, built on Ubuntu with Python, that acts as an intelligent SMS responder. Utilizing the Twilio API, it efficiently manages both incoming and outgoing SMS messages, allowing users to query information through a simple text interface. In combination with OpenAI's API models, the application offers natural language processing and conversation generation, crafting automated replies based on users' specific questions and needs. Furthermore, Google's SERP API enables the system to extract answers directly from search engine results, broadening its information base.

Designed with a meticulous focus on real-time information retrieval, the SMS LLM assistant performs immediate data processing and validation. When a query is received, the application swiftly extracts the user's phone number and message content. Relevant data, such as user history and assistant information, is retrieved from a MySQL database, ensuring personalized and contextual responses. Through its complex integration with third-party APIs like Twilio, OpenAI, and SERP, the system provides dynamic and intelligent conversation, all while maintaining robust data management capabilities. Whether it's a quick answer from the web or a more personalized interaction, the SMS LLM assistant handles it all in real time, providing a seamless and versatile user experience.


# Requirements:

 - Twilio API and SMS number - https://www.twilio.com/en-us/messaging/channels/sms
 - OpenAI API - https://platform.openai.com/
 - SerpAPI API - https://serpapi.com/
 - Ubuntu VM with Public IP - https://www.vultr.com/products/cloud-compute/
 - A DNS Domain (example.com)


# Pre Setup Tasks

 - Get an OpenAI API Key. Follow this guide: https://www.howtogeek.com/885918/how-to-get-an-openai-api-key/

 - Get a SerpAPI API Key. Basically you need a free Serpapi.com account, then your API Key is on this page: https://serpapi.com/dashboard 

 - Get a VM setup running Ubuntu 20.04 or 22.04, with a public IP. I suggest Vultr.com as its so cheap. 

 - Create a DNS A Record in your DOMAIN (eg. example.com) for a new HOST (eg. sms) and point it at the VM's Public IP from the pervios step. (sms.example.com)


# Support
Since I am extremely lazy I am not going to offer any support. Well maybe every once-n-a while. It really depends on my mood.

That being said, time was spent documenting each script. This should allow the scripts to be easily understood and modified if needed.


# Donations
Many Bothans died getting this GPT4 SMS Assistant system with realtime info lookup to you, honor them by sending me some Bitcoin(BTC). ;)

BTC: 1K4N5msYZHse6Hbxz4oWUjwqPf8wu6ducV


# License
Released under the GNU General Public License v3.

http://www.gnu.org/licenses/gpl-3.0.html
