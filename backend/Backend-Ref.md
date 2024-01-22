# 🧱 Backend Overview 
This file covers:
1. Additional setup
2. Third party services overview
3. Overall architecture
4. Data models
5. API endpoints

Note that this file assumes that you have already set up and built the project. If this is not the case, please refer to `/Lionsentry/README.md`

If you are looking for DevOps related documentation, see `/Lionsentry/DevOps-Overview.md`

## Addintional Setup 🔨

In addition to everything you've set up thusfar, you'll need to get set up with Firebase. To do this, you'll need to follow these steps:
1. Make sure that you've been added to the LionSentry Firebase project. If you haven't, please reach out to Griffin Clark on Slack and he'll add you in. 
2. Ensure that Firebase CLI tools are installed on your machine with `npm install -g firebase-tools`
3. Log in with `firebase login`
   1. Test that the CLI has been installed properly by running `firebase projects:list`. You should see a table that looks something like this:
        | Project Name | Project ID | Project Number | Location |
        |--------------|------------|----------------|----------|
        | LionSentry   | lionsentry | 698608142785   | us-central |

At this stage in the project, this step is really only relevant for setting up Firestore Indexes. However, as we expand what we're doing and use more Firebase services, it'll become more important

## Third Party Services Overview 🌎
1. Firebase - our cloud provider. Owned by Google, it provides us with an easy way to manage user authentication and data storage
   1. Authentication - used for user authentication and token generation. Currently, we only support creating users with username and password but eventually we'll support logging in with various social services
   2. Firestore - a noSQL database used for storing all application data. 
2. OpenAI APIs
   1. GPT - used for all text content generation


## Overall Architecture 🐳
Our backend was set up on Docker with a hybrid approach, trying to use the advantages that monolithic and microservice architectures provide. Microservice architectures offer logical seperations between services and the ability to scale different parts of the application indipendently. However, they suffer from increased complexity and network latency issues. Monolithic applications are much simpler and suffer no network latency issues in this sense, but spinning up new instances of the application is expensive. 

Our philosophy is to try to get the best of both worlds. Currently, each of the core components of the application (client, authentication, applicaiton logic) is treated as its own service. 

### Client 🖥️
This container holds our website, and exposes `19006` for the React website.

### Authentication Server 🙋
This server talks is responsible for everything related to user creation and logging users in/out. The client talks to this server whenever we need to create a new user, log in an existing user, get a user token, or delete a user. It works with Firebase Authentication, but does not talk to Firestore at all. 

### App Server 🧠
Where all of the interesting app logic is handled. Anything related to saving data in Firestore (updated user information, Why Statements, Devotionals, etc.) or generating content happens in this server

## Data Models 📦
See our ERD and details on what data is stored where [here](https://docs.google.com/document/d/1Hi73ZSRD2e5h5Qus8kJCieFC4FRrIhihTk54NkyeNu0/edit?usp=sharing)

## API Endpoints 🔌
**Auth Server Documentation:**
[here](https://docs.google.com/document/d/177cyiKVQTO0eRDhfEOIEDn3svhMe5fxSnG19kXdawEw/edit)

**App Server Documentation:**
[here](https://docs.google.com/document/d/1-XEgF2-u5OceDHHHec_riqOS7SYrqvcMNyNjPPdthf4/edit)