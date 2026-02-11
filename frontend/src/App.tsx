import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';
import { AppProvider } from '@contexts/AppContext';
import MainLayout from '@components/layout/MainLayout';
import HomePage from '@pages/HomePage';
import UploadPage from '@pages/UploadPage';
import ConvertPage from '@pages/ConvertPage';
import DownloadPage from '@pages/DownloadPage';
import PremiumPage from '@pages/PremiumPage';
import ProfilePage from '@pages/ProfilePage';
import LoginPage from '@pages/LoginPage';
import RegisterPage from '@pages/RegisterPage';

function App() {
  return (
    <AppProvider>
      <Router>
        <Routes>
          <Route
            path="/"
            element={
              <MainLayout>
                <HomePage />
              </MainLayout>
            }
          />
          <Route
            path="/upload"
            element={
              <MainLayout>
                <UploadPage />
              </MainLayout>
            }
          />
          <Route
            path="/convert"
            element={
              <MainLayout>
                <ConvertPage />
              </MainLayout>
            }
          />
          <Route
            path="/download"
            element={
              <MainLayout>
                <DownloadPage />
              </MainLayout>
            }
          />
          <Route
            path="/premium"
            element={
              <MainLayout>
                <PremiumPage />
              </MainLayout>
            }
          />
          <Route
            path="/profile"
            element={
              <MainLayout>
                <ProfilePage />
              </MainLayout>
            }
          />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AppProvider>
  );
}

export default App;
