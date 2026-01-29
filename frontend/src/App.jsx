import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import TrendDetail from './components/TrendDetail';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-950 text-white">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/trend/:category/:subCategory" element={<TrendDetail />} />
          <Route path="/trend/:category" element={<TrendDetail />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
