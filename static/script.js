function cerca() {
  const campo = document.getElementById('campo').value;
  const valore = document.getElementById('valore').value;
  const tipo = document.getElementById('tipo').value;

  if (valore.length < 3) {
    alert("Inserire almeno 3 lettere.");
    return;
  }

  fetch(`/cerca?campo=${campo}&valore=${valore}&tipo=${tipo}`)
    .then(res => res.json())
    .then(dati => {
      const div = document.getElementById('risultati');
      div.innerHTML = "";
      if (dati.length === 0) {
        div.innerHTML = "Nessun risultato trovato.";
        return;
      }
      dati.forEach(row => {
        div.innerHTML += `<p>${row.cognome} ${row.nome} - Nato a ${row.luogo_nascita} il ${row.data_nascita}</p>`;
      });
    });
}