async function runStep(step) {
  const res = await fetch(`/supervise/${step}/y`, { method: "POST" });
  const data = await res.json();
  console.log(data);
}

document.getElementById("steps").innerHTML = `
  <button onclick="runStep('burn')">Run Burn</button>
  <button onclick="runStep('ignite')">Run Ignite</button>
  <button onclick="runStep('residue')">Run Residue</button>
`;
