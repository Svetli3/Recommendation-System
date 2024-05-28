const sqlite3 = require('sqlite3').verbose();

const db = new sqlite3.Database('./gpus_test.db', sqlite3.OPEN_READWRITE, (err) => {
    if (err) return console.error(err.message);
});

async function searchByBrand(brand)
{
    return new Promise((resolve, reject) => {
        const query = `SELECT * FROM gpus_tb WHERE brand = (?)`;
        db.all(query, [brand], (err, rows) => {
            if (err) {
                reject(err); // Reject the Promise if there's an error
            } else {
                resolve(rows); // Resolve the Promise with the retrieved rows
            }
        });
    });
}

async function getAllGPUs() {
    return new Promise((resolve, reject) => {
        const query = `SELECT * FROM gpus_tb`;
        db.all(query, [], (err, rows) => {
            if (err) {
                reject(err); // Reject the Promise if there's an error
            } else {
                resolve(rows); // Resolve the Promise with the retrieved rows
            }
        });
    });
}

// Calculates the overall score of the gpu, score is calculated by multiplying all calculated scores together;
// using only the metrics the user has selected to search by. 
async function addGpuScores(userInput, searchOptions)
{
    let gpus = [];
    if ( 
        (userInput.brand !== '' && searchOptions.brand) || 
        (userInput.brand !== null && searchOptions.brand)  || 
        (userInput.brand !== undefined && searchOptions.brand) 
    ) {
        gpus = await searchByBrand(userInput.brand);
    }else{
        
        gpus = await getAllGPUs();
    }

    for (const gpu of gpus)
    {
        //console.log(gpu);
        let score = await calculateGpuScore(userInput, gpu, searchOptions);
        gpu.score = score;
    }
    
    return gpus;
}

async function calculateGpuScore(userInput, gpu, searchOptions)
{
    let scores = []

    if (searchOptions.clockSpeed) 
    {
        let clockSpeedScore = await calculateClockSpeedScore(userInput.clockSpeed, gpu.clock_speed);
        scores.push(clockSpeedScore); 
    }
    if (searchOptions.memorySpeed)
    {
        let memorySpeedScore = await calculateMemorySpeedScore(userInput.memorySpeed, gpu.memory_speed);
        scores.push(memorySpeedScore);
    }
    if (searchOptions.memorySize)
    {
        let memorySizeScore = await calculateMemorySizeScore(userInput.memorySize, gpu.memory_size);
        scores.push(memorySizeScore);
    }
    if (searchOptions.busWidth) 
    { 
        let busWidthScore = await calculateBusWidthScore(userInput.busWidth, gpu.bus_width);
        scores.push(busWidthScore);
    }
    if (searchOptions.price)
    {
        let priceScore = await calculatePriceScore(userInput.price, gpu.price);
        scores.push(priceScore);
    }

    let productOfScores = scores.reduce((acc, curr) => acc * curr, 1);

    return productOfScores;
}

function getTopThreeGpusByScore(gpusWithScores)
{
    // Sort the array in descending order based on the score
    gpusWithScores.sort((a, b) => b.score - a.score);

    // Slice the top three elements
    const topThree = gpusWithScores.slice(0, 3);

    return topThree;
}

// Returns a value between 0 and 1, the closer the price is to the GPU price, the higher the score (closer to 1) 
function calculatePriceScore(userPrice, gpuPrice)
{
    // Convert prices to numbers (assuming they are in the format '£xxx.xx')
    const userPriceNum = parseFloat(userPrice);
    const gpuPriceNum = parseFloat(gpuPrice.substring(1));

    // Calculate the difference between the user's price and GPU's price
    const priceDifference = Math.abs(userPriceNum - gpuPriceNum);

    // Normalise the price difference to a score between 0 and 1
    const maxDifference = 50; // Maximum acceptable price difference
    const normalizedDifference = Math.min(priceDifference / maxDifference, 1);

    // Invert the score (closer prices yield higher scores)
    const priceScore = 1 - normalizedDifference;

    return priceScore;
}

function calculateClockSpeedScore(userClockSpeed, gpuClockSpeed) {
    // Convert clock speeds to MHz (assuming they are in the format 'xxx MHz')
    const userClockSpeedMHz = parseFloat(userClockSpeed);
    const gpuClockSpeedMHz = parseFloat(gpuClockSpeed.split(' ')[0]);

    // Calculate the difference between the user's clock speed and GPU's clock speed
    const clockSpeedDifference = Math.abs(userClockSpeedMHz - gpuClockSpeedMHz);

    // Normalise the clock speed difference to a score between 0 and 1
    const maxDifference = 300; // Maximum acceptable clock speed difference
    const normalizedDifference = Math.min(clockSpeedDifference / maxDifference, 1);

    // Invert the score (closer clock speeds yield higher scores)
    const clockSpeedScore = 1 - normalizedDifference;

    return clockSpeedScore;
}

function calculateMemorySpeedScore(userMemorySpeed, gpuMemorySpeed)
{
    // Convert memory speeds to MHz (assuming they are in the format 'xxx MHz')
    const userMemorySpeedMHz = parseFloat(userMemorySpeed);
    const gpuMemorySpeedMHz = parseFloat(gpuMemorySpeed.split(' ')[0]);

    // Calculate the difference between the user's memory speed and GPU's memory speed
    const memorySpeedDifference = Math.abs(userMemorySpeedMHz - gpuMemorySpeedMHz);

    // Normalise the memory speed difference to a score between 0 and 1
    const maxDifference = 300; // Maximum acceptable memory speed difference
    const normalizedDifference = Math.min(memorySpeedDifference / maxDifference, 1);

    // Invert the score (closer memory speeds yield higher scores)
    const memorySpeedScore = 1 - normalizedDifference;

    return memorySpeedScore;
}

function calculateMemorySizeScore(userMemorySize, gpuMemorySize)
{
    // Extract memory sizes (assuming they are in the format 'x GB')
    const userMemorySizeGB = parseInt(userMemorySize);
    const gpuMemorySizeGB = parseInt(gpuMemorySize.split(' ')[0]);

    // Calculate the difference between the user's memory size and GPU's memory size
    const memorySizeDifference = Math.abs(userMemorySizeGB - gpuMemorySizeGB);

    // Normalise the memory size difference to a score between 0 and 1
    const maxDifference = 8; // Maximum acceptable memory size difference in GB
    const normalizedDifference = Math.min(memorySizeDifference / maxDifference, 1);

    // Invert the score (closer memory sizes yield higher scores)
    const memorySizeScore = 1 - normalizedDifference;

    return memorySizeScore;
}

function calculateBusWidthScore(userBusWidth, gpuBusWidth)
{
    // Extract bus widths (assuming they are in the format 'xxx bit')
    const userBusWidthBits = parseInt(userBusWidth.split(' ')[0]);
    const gpuBusWidthBits = parseInt(gpuBusWidth.split(' ')[0]);

    // Calculate the difference between the user's bus width and GPU's bus width
    const busWidthDifference = Math.abs(userBusWidthBits - gpuBusWidthBits);

    // Normalise the bus width difference to a score between 0 and 1
    const maxDifference = 64; // Maximum acceptable bus width difference in bits
    const normalizedDifference = Math.min(busWidthDifference / maxDifference, 1);

    // Invert the score (closer bus widths yield higher scores)
    const busWidthScore = 1 - normalizedDifference;

    return busWidthScore;
}

module.exports = {
    addGpuScores,
    getTopThreeGpusByScore
};