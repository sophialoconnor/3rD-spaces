import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [scrapeStatus, setScrapeStatus] = useState(null);
  const [stats, setStats] = useState(null);
  const [recentContent, setRecentContent] = useState([]);

  useEffect(() => {
    // Get initial scrape status and stats
    fetchScrapeStatus();
    fetchStats();
    fetchRecentContent();
  }, []);

  const fetchScrapeStatus = async () => {
    try {
      const response = await axios.get(`${API}/scrape/status`);
      setScrapeStatus(response.data);
    } catch (error) {
      console.error('Error fetching scrape status:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/content/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchRecentContent = async () => {
    try {
      const response = await axios.get(`${API}/content/recent`);
      setRecentContent(response.data.slice(0, 5)); // Show top 5 recent items
    } catch (error) {
      console.error('Error fetching recent content:', error);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const response = await axios.post(`${API}/search`, {
        query: searchQuery,
        limit: 10
      });
      setSearchResults(response.data);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const triggerScrape = async () => {
    try {
      await axios.post(`${API}/scrape`);
      alert('Scraping started! This may take a few minutes.');
      // Refresh status after a delay
      setTimeout(() => {
        fetchScrapeStatus();
        fetchStats();
        fetchRecentContent();
      }, 3000);
    } catch (error) {
      console.error('Error triggering scrape:', error);
      alert('Failed to start scraping');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString();
  };

  const getSourceName = (url) => {
    try {
      const domain = new URL(url).hostname;
      return domain.replace('www.', '');
    } catch {
      return 'Unknown';
    }
  };

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#ffff00' }}>
      {/* Header */}
      <div className="relative overflow-hidden">
        <div className="relative z-10 container mx-auto px-4 py-8">
          <div className="text-center">
            <div className="text-4xl md:text-6xl font-bold text-black mb-6 chrome-text">
              3rD Spaces
            </div>
            
            {/* Search Bar */}
            <form onSubmit={handleSearch} className="max-w-2xl mx-auto mb-8">
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search... Dublin, IE"
                  className="w-full px-6 py-4 text-lg rounded-full border-2 border-gray-300 focus:border-gray-500 focus:outline-none shadow-lg"
                />
                <button
                  type="submit"
                  className="absolute right-2 top-2 px-6 py-2 bg-gray-600 text-white rounded-full hover:bg-gray-700 transition-colors"
                  disabled={loading}
                >
                  {loading ? '...' : '🔍'}
                </button>
              </div>
            </form>

            {/* Tagline */}
            <div className="text-lg md:text-xl text-black mb-6 max-w-2xl mx-auto">
              <p className="font-bold">3rd space definition</p>
              <p className="font-bold">life in 3D, become chronically offline</p>
              <p className="font-bold">
                find free cultural events for young people in less than 30 seconds
              </p>
            </div>

            {/* Liminal Space Image */}
            <div className="mb-8">
              <img 
                src="https://images.unsplash.com/photo-1684895309257-dc0facb0eecc?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHwzfHxsaW1pbmFsJTIwc3BhY2V8ZW58MHx8fHwxNzUzNTMxODE1fDA&ixlib=rb-4.1.0&q=85"
                alt="Liminal Space"
                className="mx-auto rounded-lg shadow-lg max-w-md w-full"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        {/* Status Section */}
        <div className="mb-8 bg-white bg-opacity-80 rounded-lg p-6 shadow-lg">
          <div className="flex flex-col md:flex-row justify-between items-center mb-4">
            <h3 className="text-2xl font-bold text-purple-800 mb-4 md:mb-0">Database Status</h3>
            <button
              onClick={triggerScrape}
              className="px-6 py-2 bg-purple-600 text-white rounded-full hover:bg-purple-700 transition-colors"
            >
              Refresh Data
            </button>
          </div>
          
          {scrapeStatus && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-purple-100 p-4 rounded-lg">
                <h4 className="font-bold text-purple-800">Status</h4>
                <p className="text-purple-600">{scrapeStatus.status}</p>
              </div>
              <div className="bg-purple-100 p-4 rounded-lg">
                <h4 className="font-bold text-purple-800">Articles</h4>
                <p className="text-purple-600">{scrapeStatus.scraped_count}</p>
              </div>
              <div className="bg-purple-100 p-4 rounded-lg">
                <h4 className="font-bold text-purple-800">Last Updated</h4>
                <p className="text-purple-600">
                  {scrapeStatus.last_scraped ? formatDate(scrapeStatus.last_scraped) : 'Never'}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="mb-8 bg-white bg-opacity-80 rounded-lg p-6 shadow-lg">
            <h3 className="text-2xl font-bold text-purple-800 mb-6">Search Results</h3>
            <div className="space-y-4">
              {searchResults.map((result) => (
                <div key={result.id} className="border-b border-purple-200 pb-4">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="text-lg font-semibold text-purple-800 hover:text-purple-600">
                      <a href={result.url} target="_blank" rel="noopener noreferrer">
                        {result.title}
                      </a>
                    </h4>
                    <span className="text-sm text-purple-500 ml-4">
                      {(result.relevance_score * 100).toFixed(0)}% match
                    </span>
                  </div>
                  <p className="text-gray-700 mb-2">{result.description}</p>
                  <div className="flex flex-wrap gap-2 text-sm text-purple-600">
                    <span>{getSourceName(result.source_website)}</span>
                    <span>•</span>
                    <span>{result.content_type}</span>
                    {result.venue && (
                      <>
                        <span>•</span>
                        <span>{result.venue}</span>
                      </>
                    )}
                    {result.event_date && (
                      <>
                        <span>•</span>
                        <span>{formatDate(result.event_date)}</span>
                      </>
                    )}
                  </div>
                  {result.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {result.tags.map((tag, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-purple-200 text-purple-800 rounded-full text-xs"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Content */}
        {recentContent.length > 0 && (
          <div className="mb-8 bg-white bg-opacity-80 rounded-lg p-6 shadow-lg">
            <h3 className="text-2xl font-bold text-purple-800 mb-6">Latest Dublin Culture</h3>
            <div className="space-y-4">
              {recentContent.map((content) => (
                <div key={content.id} className="border-b border-purple-200 pb-4">
                  <h4 className="text-lg font-semibold text-purple-800 hover:text-purple-600">
                    <a href={content.url} target="_blank" rel="noopener noreferrer">
                      {content.title}
                    </a>
                  </h4>
                  <p className="text-gray-700 mb-2">{content.description}</p>
                  <div className="flex flex-wrap gap-2 text-sm text-purple-600">
                    <span>{getSourceName(content.source_website)}</span>
                    <span>•</span>
                    <span>{content.content_type}</span>
                    <span>•</span>
                    <span>{formatDate(content.scraped_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Stats */}
        {stats && (
          <div className="mb-8 bg-white bg-opacity-80 rounded-lg p-6 shadow-lg">
            <h3 className="text-2xl font-bold text-purple-800 mb-6">Database Statistics</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-lg font-semibold text-purple-800 mb-3">Content Types</h4>
                <div className="space-y-2">
                  {Object.entries(stats.by_type || {}).map(([type, count]) => (
                    <div key={type} className="flex justify-between">
                      <span className="text-purple-600">{type}</span>
                      <span className="font-semibold">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h4 className="text-lg font-semibold text-purple-800 mb-3">Sources</h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {Object.entries(stats.by_source || {}).map(([source, count]) => (
                    <div key={source} className="flex justify-between">
                      <span className="text-purple-600 text-sm">{getSourceName(source)}</span>
                      <span className="font-semibold">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="bg-purple-800 text-white py-8 mt-12">
        <div className="container mx-auto px-4 text-center">
          <p className="text-lg font-semibold mb-2">Dublin Cultural Events Search Engine</p>
          <p className="text-purple-200">Discovering 3rd spaces and cultural events in Dublin</p>
        </div>
      </footer>
    </div>
  );
};

export default App;