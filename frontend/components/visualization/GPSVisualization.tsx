export default function GPSVisualization() {
  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">GPS Visualisering</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-100 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Rutekart</h3>
          <div className="chart-container bg-white rounded border-2 border-dashed border-gray-300 flex items-center justify-center">
            <p className="text-gray-500">Interaktivt kart kommer her</p>
          </div>
        </div>
        
        <div className="bg-gray-100 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Høydeprofil</h3>
          <div className="chart-container bg-white rounded border-2 border-dashed border-gray-300 flex items-center justify-center">
            <p className="text-gray-500">Høydediagram kommer her</p>
          </div>
        </div>
        
        <div className="bg-gray-100 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Hastighetsanalyse</h3>
          <div className="chart-container bg-white rounded border-2 border-dashed border-gray-300 flex items-center justify-center">
            <p className="text-gray-500">Hastighetsdiagram kommer her</p>
          </div>
        </div>
        
        <div className="bg-gray-100 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Statistikk</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Total distanse:</span>
              <span className="font-medium">15.2 km</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Gjennomsnittsfart:</span>
              <span className="font-medium">12.4 km/h</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Maks høyde:</span>
              <span className="font-medium">342 m</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Total tid:</span>
              <span className="font-medium">1t 14min</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 