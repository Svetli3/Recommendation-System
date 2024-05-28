const express = require('express');
const router = express.Router();

let topThree;

function setTopThree(t)
{
    topThree = t;
}

router.get('/', async (req, res) => {

    const data = {topThree};
    
    res.json(data);
});

module.exports = { 
    router: router,
    setTopThree: setTopThree
  }