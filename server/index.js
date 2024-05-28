const express = require('express');
const app = express();
const bodyParser = require('body-parser');

const PORT = 3001;

//Routers
const searchRouter = require('./routes/searchRouter.js');
const recommendationsRouter = require('./routes/recommendationsRouter.js');


// Middleware to parse form data
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

//Routes
app.use('/search', searchRouter);
app.use('/recommendations', recommendationsRouter.router);

app.listen(PORT, () => {console.log(`Server listening on port ${PORT}`);});