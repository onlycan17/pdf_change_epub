import type { FC, ReactNode } from 'react';
import {
  createBrowserRouter,
  Navigate,
  RouterProvider,
  useLocation,
} from 'react-router-dom';
import { AppProvider } from '@contexts/AppContext';
import MainLayout from '@components/layout/MainLayout';
import HomePage from '@pages/HomePage';
import UploadPage from '@pages/UploadPage';
import ConvertPage from '@pages/ConvertPage';
import DownloadPage from '@pages/DownloadPage';
import SupportPage from '@pages/SupportPage';
import HelpCenterPage from '@pages/HelpCenterPage';
import ContactPage from '@pages/ContactPage';
import TermsPage from '@pages/TermsPage';
import PrivacyPage from '@pages/PrivacyPage';
import ServiceGuidePage from '@pages/ServiceGuidePage';
import ProfilePage from '@pages/ProfilePage';
import LoginPage from '@pages/LoginPage';
import RegisterPage from '@pages/RegisterPage';
import LargeFileRequestPage from '@pages/LargeFileRequestPage';
import LargeFileRequestsAdminPage from '@pages/LargeFileRequestsAdminPage';
import AdminDashboardPage from '@pages/AdminDashboardPage';
import { hasUsableAuthToken } from '@utils/subscription';

type RequireAuthProps = {
  children: ReactNode;
};

const RequireAuth: FC<RequireAuthProps> = ({ children }) => {
  const location = useLocation();
  const isAuthenticated = hasUsableAuthToken();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <>{children}</>;
};

const RequireGuest: FC<RequireAuthProps> = ({ children }) => {
  const isAuthenticated = hasUsableAuthToken();

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

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
        <RequireAuth>
          <MainLayout>
            <ConvertPage />
          </MainLayout>
        </RequireAuth>
      ),
    },
    {
      path: '/download',
      element: (
        <RequireAuth>
          <MainLayout>
            <DownloadPage />
          </MainLayout>
        </RequireAuth>
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
      path: '/service-guide',
      element: (
        <MainLayout>
          <ServiceGuidePage />
        </MainLayout>
      ),
    },
    {
      path: '/help-center',
      element: (
        <MainLayout>
          <HelpCenterPage />
        </MainLayout>
      ),
    },
    {
      path: '/contact',
      element: (
        <MainLayout>
          <ContactPage />
        </MainLayout>
      ),
    },
    {
      path: '/terms',
      element: (
        <MainLayout>
          <TermsPage />
        </MainLayout>
      ),
    },
    {
      path: '/privacy',
      element: (
        <MainLayout>
          <PrivacyPage />
        </MainLayout>
      ),
    },
    {
      path: '/profile',
      element: (
        <RequireAuth>
          <MainLayout>
            <ProfilePage />
          </MainLayout>
        </RequireAuth>
      ),
    },
    {
      path: '/large-file-request',
      element: (
        <MainLayout>
          <LargeFileRequestPage />
        </MainLayout>
      ),
    },
    {
      path: '/large-file-requests',
      element: (
        <RequireAuth>
          <MainLayout>
            <LargeFileRequestsAdminPage />
          </MainLayout>
        </RequireAuth>
      ),
    },
    {
      path: '/admin/dashboard',
      element: (
        <RequireAuth>
          <MainLayout>
            <AdminDashboardPage />
          </MainLayout>
        </RequireAuth>
      ),
    },
    {
      path: '/login',
      element: (
        <RequireGuest>
          <LoginPage />
        </RequireGuest>
      ),
    },
    {
      path: '/register',
      element: (
        <RequireGuest>
          <RegisterPage />
        </RequireGuest>
      ),
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
