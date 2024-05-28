const express = require('express');
const router = express.Router();

const recommendationsRouter = require('./recommendationsRouter.js');
const db = require('../database.js');

router.post('/', async (req, res) => {
 
    userInput = req.body.formData;
    searchParameters = req.body.options;

    let gpuScores = await db.addGpuScores(userInput, searchParameters);
    let topThree = await db.getTopThreeGpusByScore(gpuScores);

    recommendationsRouter.setTopThree(topThree);

    res.json({ redirectTo: '/recommendations' });
});

module.exports = router;