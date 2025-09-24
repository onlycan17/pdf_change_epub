import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AppProvider } from '@contexts/AppContext'
import MainLayout from '@components/layout/MainLayout'
import HomePage from '@pages/HomePage'
import UploadPage from '@pages/UploadPage'
import ConvertPage from '@pages/ConvertPage'
import DownloadPage from '@pages/DownloadPage'
import PremiumPage from '@pages/PremiumPage'
import ProfilePage from '@pages/ProfilePage'
import LoginPage from '@pages/LoginPage'
import RegisterPage from '@pages/RegisterPage'

function App() {
  return (
    <AppProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="*" element={
            <MainLayout>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/upload" element={<UploadPage />} />
                <Route path="/convert" element={<ConvertPage />} />
                <Route path="/download" element={<DownloadPage />} />
                <Route path="/premium" element={<PremiumPage />} />
                <Route path="/profile" element={<ProfilePage />} />
              </Routes>
            </MainLayout>
          } />
        </Routes>
      </Router>
    </AppProvider>
  )
}

export default App