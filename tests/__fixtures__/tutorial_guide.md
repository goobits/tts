# How to Build Your First Web Application

## Introduction

Welcome to this step-by-step tutorial! Today, we'll learn how to create a simple web application from scratch. Don't worry if you're new to programming - we'll take it slow and explain everything along the way.

## What You'll Need

Before we begin, let's make sure you have everything set up:

1. A text editor (we recommend VS Code)
2. Node.js installed on your computer
3. A web browser (Chrome or Firefox)
4. About 30 minutes of your time

## Step 1: Setting Up Your Project

First, let's create a new folder for our project. Open your terminal and follow these commands:

```bash
mkdir my-first-app
cd my-first-app
npm init -y
```

Great! You've just created your project folder and initialized it. Let me explain what we just did:
- `mkdir` creates a new directory
- `cd` changes into that directory
- `npm init -y` creates a package.json file with default settings

## Step 2: Installing Dependencies

Now, let's install Express, which will help us create our web server:

```bash
npm install express
```

This command downloads Express and adds it to your project. You'll see a new folder called `node_modules` appear - that's perfectly normal!

## Step 3: Creating Your First Server

Let's create a file called `app.js`. Open your text editor and type the following:

```javascript
const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
  res.send('Hello World!');
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
```

Let me break this down for you:
- Line 1: We import Express
- Line 2: We create our application
- Line 3: We set the port number
- Lines 5-7: We create a route that responds to web requests
- Lines 9-11: We start the server

## Step 4: Running Your Application

Now for the exciting part! Let's run your application:

```bash
node app.js
```

You should see: "Server running at http://localhost:3000"

Open your web browser and go to that address. You should see "Hello World!" - congratulations, you've just created your first web application!

## Step 5: Adding More Features

Let's add another page to your application. Add this code after your first route:

```javascript
app.get('/about', (req, res) => {
  res.send('This is the about page!');
});
```

Now restart your server (press Ctrl+C to stop, then run `node app.js` again) and visit http://localhost:3000/about

## What's Next?

Excellent work! You've just built your first web application. Here are some things you can try next:

1. Add more routes to your application
2. Learn how to serve HTML files
3. Add some CSS to make it look nice
4. Connect a database

Remember, learning to code is a journey. Take it one step at a time, and don't be afraid to experiment!

## Troubleshooting

If something doesn't work:
- Make sure you saved all your files
- Check for typos in your code
- Ensure Node.js is properly installed
- Try restarting your terminal

Happy coding! 🎉