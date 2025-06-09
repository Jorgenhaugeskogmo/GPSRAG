export default function Test() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
      <div className="bg-white p-8 rounded-2xl shadow-xl">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">Tailwind Test</h1>
        <p className="text-gray-600">Hvis du ser farger og styling, fungerer Tailwind!</p>
        <button className="mt-4 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
          Test Knapp
        </button>
      </div>
    </div>
  );
} 