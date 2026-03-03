import {
  createBrowserRouter,
  Navigate,
  RouterProvider,
} from 'react-router-dom';
import { AppProvider } from '@contexts/AppContext';
import MainLayout from '@components/layout/MainLayout';
import HomePage from '@pages/HomePage';
import UploadPage from '@pages/UploadPage';
import ConvertPage from '@pages/ConvertPage';
import DownloadPage from '@pages/DownloadPage';
import SupportPage from '@pages/SupportPage';
import ProfilePage from '@pages/ProfilePage';
import LoginPage from '@pages/LoginPage';
import RegisterPage from '@pages/RegisterPage';

const router = createBrowserRouter(
  [
    {
      path: '/',
      element: (
        <MainLayout>
          <HomePage />
        </MainLayout>
      ),
    },
    {
      path: '/upload',
      element: (
        <MainLayout>
          <UploadPage />
        </MainLayout>
      ),
    },
    {
      path: '/convert',
      element: (
        <MainLayout>
          <ConvertPage />
        </MainLayout>
      ),
    },
    {
      path: '/download',
      element: (
        <MainLayout>
          <DownloadPage />
        </MainLayout>
      ),
    },
    {
      path: '/premium',
      element: <Navigate to="/support" replace />,
    },
    {
      path: '/support',
      element: (
        <MainLayout>
          <SupportPage />
        </MainLayout>
      ),
    },
    {
      path: '/profile',
      element: (
        <MainLayout>
          <ProfilePage />
        </MainLayout>
      ),
    },
    {
      path: '/login',
      element: <LoginPage />,
    },
    {
      path: '/register',
      element: <RegisterPage />,
    },
    {
      path: '/payment/billing/success',
      element: <Navigate to="/support" replace />,
    },
    {
      path: '/payment/billing/fail',
      element: <Navigate to="/support" replace />,
    },
    {
      path: '*',
      element: <Navigate to="/" replace />,
    },
  ],
  {
    future: {
      v7_relativeSplatPath: true,
    },
  }
);

function App() {
  return (
    <AppProvider>
      <RouterProvider router={router} future={{ v7_startTransition: true }} />
    </AppProvider>
  );
}

export default App;
