import { syntheticDemo, toCSV } from "../backend/scandoc/model.js";

const demo = await syntheticDemo();
if (process.argv.includes("--csv")) process.stdout.write(toCSV(demo));
else process.stdout.write(JSON.stringify(demo, null, 2) + "\n");
