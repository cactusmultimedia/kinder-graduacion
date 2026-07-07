const XLSX = require("xlsx");

const preguntas = [
  { materia: "Español", pregunta: '¿Cuál es la letra con la que empieza la palabra "árbol"?', o1: "o", o2: "a", o3: "e", o4: "i", correcta: 2 },
  { materia: "Español", pregunta: "¿Cuál de estas palabras está escrita correctamente?", o1: "kasa", o2: "cassa", o3: "caza", o4: "casa", correcta: 4 },
  { materia: "Español", pregunta: '¿Cuál es el plural de "lápiz"?', o1: "lapizes", o2: "lapices", o3: "lápizes", o4: "lápices", correcta: 4 },
  { materia: "Español", pregunta: "¿Qué signo se usa al final de una pregunta?", o1: ",", o2: ".", o3: "!", o4: "?", correcta: 4 },
  { materia: "Español", pregunta: '¿Cuál es el sinónimo de "feliz"?', o1: "triste", o2: "enojado", o3: "cansado", o4: "contento", correcta: 4 },
  { materia: "Español", pregunta: '¿Cuántas sílabas tiene la palabra "manzana"?', o1: "1", o2: "3", o3: "2", o4: "4", correcta: 2 },
  { materia: "Español", pregunta: '¿Qué artículo es el correcto? "___ casa es bonita"', o1: "Los", o2: "La", o3: "El", o4: "Las", correcta: 2 },
  { materia: "Español", pregunta: '¿Cuál es el antónimo de "grande"?', o1: "largo", o2: "alto", o3: "pequeño", o4: "pesado", correcta: 3 },
  { materia: "Matemáticas", pregunta: "¿Cuánto es 5 + 3?", o1: "6", o2: "7", o3: "9", o4: "8", correcta: 4 },
  { materia: "Matemáticas", pregunta: "¿Cuánto es 10 - 4?", o1: "8", o2: "5", o3: "6", o4: "7", correcta: 3 },
  { materia: "Matemáticas", pregunta: "¿Cuál número es el más grande?", o1: "45", o2: "89", o3: "72", o4: "98", correcta: 4 },
  { materia: "Matemáticas", pregunta: "¿Cuántos lados tiene un cuadrado?", o1: "4", o2: "6", o3: "3", o4: "5", correcta: 1 },
  { materia: "Matemáticas", pregunta: "¿Cuánto es el doble de 7?", o1: "18", o2: "12", o3: "14", o4: "16", correcta: 3 },
  { materia: "Matemáticas", pregunta: "¿Qué número falta en la serie? 10, 20, __, 40", o1: "35", o2: "15", o3: "25", o4: "30", correcta: 4 },
  { materia: "Matemáticas", pregunta: "¿Cuánto es 2 + 2 + 2?", o1: "3", o2: "6", o3: "8", o4: "4", correcta: 2 },
  { materia: "Matemáticas", pregunta: "¿Cuántas patas tienen dos perros?", o1: "8", o2: "12", o3: "6", o4: "4", correcta: 1 },
  { materia: "Conocimiento del Medio", pregunta: "¿Qué parte de la planta está debajo de la tierra?", o1: "la flor", o2: "la raíz", o3: "el tallo", o4: "la hoja", correcta: 2 },
  { materia: "Conocimiento del Medio", pregunta: "¿Cuántas patas tiene un perro?", o1: "4", o2: "8", o3: "2", o4: "6", correcta: 1 },
  { materia: "Conocimiento del Medio", pregunta: "¿Qué necesitan las plantas para crecer?", o1: "agua y sal", o2: "agua y sol", o3: "papel y lápiz", o4: "leche y pan", correcta: 2 },
  { materia: "Conocimiento del Medio", pregunta: "¿Cuál es el planeta donde vivimos?", o1: "Marte", o2: "Venus", o3: "Saturno", o4: "Tierra", correcta: 4 },
  { materia: "Conocimiento del Medio", pregunta: "¿Qué animal nos da leche?", o1: "la vaca", o2: "el perro", o3: "el gato", o4: "el gallo", correcta: 1 },
  { materia: "Conocimiento del Medio", pregunta: "¿Con qué sentido olemos?", o1: "los oídos", o2: "la nariz", o3: "los ojos", o4: "la boca", correcta: 2 },
  { materia: "Conocimiento del Medio", pregunta: "¿Para qué sirven los dientes?", o1: "ver", o2: "oir", o3: "oler", o4: "masticar", correcta: 4 },
  { materia: "Formación Cívica y Ética", pregunta: "¿Cómo debemos tratar a nuestros compañeros?", o1: "gritando", o2: "ignorándolos", o3: "empujando", o4: "con respeto", correcta: 4 },
  { materia: "Formación Cívica y Ética", pregunta: "¿Qué hacemos cuando alguien necesita ayuda?", o1: "nos reímos", o2: "lo ayudamos", o3: "lo ignoramos", o4: "nos vamos", correcta: 2 },
  { materia: "Formación Cívica y Ética", pregunta: "¿Dónde es seguro cruzar la calle?", o1: "corriendo", o2: "en el paso peatonal", o3: "en medio de la calle", o4: "entre coches", correcta: 2 },
  { materia: "Formación Cívica y Ética", pregunta: "¿Qué derecho tienen todos los niños y niñas?", o1: "a fumar", o2: "a manejar", o3: "a trabajar", o4: "a la educación", correcta: 4 },
  { materia: "Educación Socioemocional", pregunta: "¿Cómo se llama la emoción cuando estamos muy contentos?", o1: "alegría", o2: "tristeza", o3: "miedo", o4: "enojo", correcta: 1 },
  { materia: "Educación Socioemocional", pregunta: "Cuando algo nos enoja, ¿qué es mejor hacer?", o1: "pegar", o2: "gritar", o3: "llorar", o4: "respirar y calmarnos", correcta: 4 },
  { materia: "Educación Socioemocional", pregunta: "¿Cómo se siente un amigo cuando lo ayudas?", o1: "feliz", o2: "enojado", o3: "asustado", o4: "triste", correcta: 1 },
];

const letras = ["A", "B", "C", "D"];

function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

const filas = preguntas.map((p, i) => {
  const opciones = [
    { texto: p.o1, idx: 1 },
    { texto: p.o2, idx: 2 },
    { texto: p.o3, idx: 3 },
    { texto: p.o4, idx: 4 },
  ];
  shuffle(opciones);

  const correctLetter = letras[opciones.findIndex(o => o.idx === p.correcta)];

  return {
    "#": i + 1,
    Materia: p.materia,
    Pregunta: p.pregunta,
    "Opción A": opciones[0].texto,
    "Opción B": opciones[1].texto,
    "Opción C": opciones[2].texto,
    "Opción D": opciones[3].texto,
    "Respuesta correcta": correctLetter,
    Tiempo: 30,
  };
});

const wb = XLSX.utils.book_new();

const ws = XLSX.utils.json_to_sheet(filas);
ws["!cols"] = [
  { wch: 4 },   // #
  { wch: 28 },  // Materia
  { wch: 55 },  // Pregunta
  { wch: 28 },  // Opción A
  { wch: 28 },  // Opción B
  { wch: 28 },  // Opción C
  { wch: 28 },  // Opción D
  { wch: 18 },  // Respuesta correcta
  { wch: 8 },   // Tiempo
];

XLSX.utils.book_append_sheet(wb, ws, "Preguntas Kahoot");

const ws2 = XLSX.utils.aoa_to_sheet([
  ["INSTRUCCIONES - Kahoot 2° de Primaria"],
  [""],
  ["Este archivo contiene 30 preguntas para jugar Kahoot en clase."],
  [""],
  ["MATERIAS:"],
  ["  • Español (8 preguntas)"],
  ["  • Matemáticas (8 preguntas)"],
  ["  • Conocimiento del Medio (7 preguntas)"],
  ["  • Formación Cívica y Ética (4 preguntas)"],
  ["  • Educación Socioemocional (3 preguntas)"],
  [""],
  ["CÓMO USAR:"],
  ["  1. Abre kahoot.com y crea un nuevo Kahoot"],
  ["  2. Importa este archivo Excel o añade las preguntas manualmente"],
  ["  3. Las respuestas correctas están marcadas en la columna 'Respuesta correcta'"],
  ["  4. Cada pregunta tiene 30 segundos de tiempo"],
  [""],
  ["NOTA: Las opciones YA están desordenadas aleatoriamente en cada pregunta."],
  ["      La respuesta correcta aparece en una letra diferente cada vez."],
]);
ws2["!cols"] = [{ wch: 80 }];
XLSX.utils.book_append_sheet(wb, ws2, "Instrucciones");

const outPath = "/Users/navirami/Documents/archivado/kahoot_2do_primaria.xlsx";
XLSX.writeFile(wb, outPath);
console.log("Creado: " + outPath);
console.log(preguntas.length + " preguntas con opciones desordenadas");
console.log("Distribución de respuestas correctas:");
const dist = {};
filas.forEach(f => { dist[f["Respuesta correcta"]] = (dist[f["Respuesta correcta"]] || 0) + 1; });
Object.entries(dist).forEach(([k, v]) => console.log("  " + k + ": " + v));
