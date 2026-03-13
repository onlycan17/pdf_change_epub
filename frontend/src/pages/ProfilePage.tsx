import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useApp } from '@contexts/AppContext';
import {
  buildUserFromProfile,
  fetchCurrentUserProfile,
  type CurrentUserProfile,
} from '@utils/authApi';
import { getCurrentPlan } from '@utils/subscription';

const ProfilePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('profile');
  const [profile, setProfile] = useState<CurrentUserProfile | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const { state, dispatch } = useApp();
  const currentPlan = getCurrentPlan();

  useEffect(() => {
    const run = async () => {
      setIsLoadingProfile(true);
      setErrorMessage('');
      try {
        const nextProfile = await fetchCurrentUserProfile();
        if (!nextProfile) {
          setErrorMessage(
            '로그인 정보를 확인할 수 없습니다. 다시 로그인해주세요.'
          );
          dispatch({ type: 'SET_USER', payload: null });
          dispatch({ type: 'SET_AUTHENTICATED', payload: false });
          return;
        }
        setProfile(nextProfile);
        dispatch({
          type: 'SET_USER',
          payload: buildUserFromProfile(nextProfile),
        });
      } finally {
        setIsLoadingProfile(false);
      }
    };
    void run();
  }, [dispatch]);

  const derivedUser = profile ? buildUserFromProfile(profile) : state.user;
  const userData = {
    name: derivedUser?.name || '사용자',
    email: profile?.email || derivedUser?.email || '',
    joinDate: '가입일 정보 준비 중',
    subscription: `${currentPlan.label} (${currentPlan.code})`,
    conversionsThisMonth: currentPlan.isSubscribed ? 0 : 0,
    maxConversions: currentPlan.isSubscribed ? 999 : 2,
  };

  const conversionHistory = [
    {
      id: 1,
      fileName: 'document.pdf',
      status: '완료',
      date: '2024-01-20',
      size: '2.4MB',
    },
    {
      id: 2,
      fileName: 'report.pdf',
      status: '완료',
      date: '2024-01-18',
      size: '1.8MB',
    },
    {
      id: 3,
      fileName: 'book.pdf',
      status: '완료',
      date: '2024-01-15',
      size: '5.2MB',
    },
  ];

  if (isLoadingProfile) {
    return <p className="text-gray-600">프로필 정보를 불러오는 중...</p>;
  }

  if (errorMessage) {
    return (
      <div className="max-w-3xl mx-auto rounded-lg border border-red-200 bg-red-50 p-6">
        <h1 className="text-2xl font-bold text-red-900">프로필</h1>
        <p className="mt-3 text-red-700">{errorMessage}</p>
        <Link
          to="/login"
          className="mt-4 inline-flex rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
        >
          로그인 페이지로 이동
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">프로필</h1>
        <p className="text-gray-600">계정 정보와 변환 기록을 관리하세요</p>
      </div>

      <div className="grid md:grid-cols-4 gap-8">
        {/* Sidebar */}
        <div className="md:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="text-center mb-6">
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-blue-600">
                  {userData.name.charAt(0)}
                </span>
              </div>
              <h3 className="font-semibold text-gray-900">{userData.name}</h3>
              <p className="text-sm text-gray-600">{userData.email}</p>
            </div>

            <nav className="space-y-2">
              <button
                type="button"
                onClick={() => setActiveTab('profile')}
                className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'profile'
                    ? 'bg-blue-100 text-blue-600'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                프로필 정보
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('conversions')}
                className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'conversions'
                    ? 'bg-blue-100 text-blue-600'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                변환 기록
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('settings')}
                className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'settings'
                    ? 'bg-blue-100 text-blue-600'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                설정
              </button>
            </nav>
          </div>

          {/* Usage Stats */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-4">
            <h4 className="font-semibold text-gray-900 mb-4">이번 달 사용량</h4>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">변환 횟수</span>
                  <span className="text-gray-900">
                    {userData.conversionsThisMonth}/{userData.maxConversions}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{
                      width: `${(userData.conversionsThisMonth / userData.maxConversions) * 100}%`,
                    }}
                  ></div>
                </div>
              </div>
              <div className="text-sm text-gray-600">
                구독 상태:{' '}
                <span className="font-medium text-gray-900">
                  {userData.subscription}
                </span>
              </div>
              <div className="text-sm text-gray-600">
                가입일:{' '}
                <span className="font-medium text-gray-900">
                  {userData.joinDate}
                </span>
              </div>
              {profile?.is_privileged && (
                <div className="text-sm text-gray-600">
                  권한:{' '}
                  <span className="font-medium text-blue-700">운영자 계정</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="md:col-span-3">
          {activeTab === 'profile' && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">
                프로필 정보
              </h2>
              <form className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label
                      htmlFor="profile-name"
                      className="block text-sm font-medium text-gray-700 mb-2"
                    >
                      이름
                    </label>
                    <input
                      id="profile-name"
                      type="text"
                      value={userData.name}
                      readOnly
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label
                      htmlFor="profile-email"
                      className="block text-sm font-medium text-gray-700 mb-2"
                    >
                      이메일
                    </label>
                    <input
                      id="profile-email"
                      type="email"
                      value={userData.email}
                      readOnly
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                <div>
                  <label
                    htmlFor="profile-password"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    비밀번호
                  </label>
                  <input
                    id="profile-password"
                    type="password"
                    placeholder="새 비밀번호"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="flex justify-end">
                  <button
                    type="button"
                    className="bg-blue-600 text-white px-6 py-2 rounded-md font-medium hover:bg-blue-700 transition-colors"
                  >
                    저장 기능 준비 중
                  </button>
                </div>
              </form>
            </div>
          )}

          {activeTab === 'conversions' && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">
                변환 기록
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 font-semibold text-gray-900">
                        파일명
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-900">
                        상태
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-900">
                        날짜
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-900">
                        크기
                      </th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-900">
                        작업
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {conversionHistory.map((item) => (
                      <tr key={item.id} className="border-b border-gray-100">
                        <td className="py-3 px-4 text-gray-700">
                          {item.fileName}
                        </td>
                        <td className="py-3 px-4">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            {item.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-gray-700">{item.date}</td>
                        <td className="py-3 px-4 text-gray-700">{item.size}</td>
                        <td className="py-3 px-4">
                          <button
                            type="button"
                            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                          >
                            다운로드
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">설정</h2>
              <div className="space-y-6">
                <div>
                  <h3 className="font-medium text-gray-900 mb-4">
                    화면 알림 설정
                  </h3>
                  <div className="space-y-3">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        defaultChecked
                      />
                      <span className="ml-2 text-sm text-gray-700">
                        변환 완료 알림 표시
                      </span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">
                        다운로드 오류 알림 표시
                      </span>
                    </label>
                  </div>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 mb-4">
                    기본 변환 설정
                  </h3>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label
                        htmlFor="default-language"
                        className="block text-sm font-medium text-gray-700 mb-2"
                      >
                        기본 언어
                      </label>
                      <select
                        id="default-language"
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="ko">한국어</option>
                        <option value="en">영어</option>
                      </select>
                    </div>
                    <div>
                      <label
                        htmlFor="image-quality"
                        className="block text-sm font-medium text-gray-700 mb-2"
                      >
                        이미지 품질
                      </label>
                      <select
                        id="image-quality"
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="medium">중간</option>
                        <option value="high">높음</option>
                        <option value="low">낮음</option>
                      </select>
                    </div>
                  </div>
                </div>
                <div className="flex justify-end">
                  <button
                    type="button"
                    className="bg-blue-600 text-white px-6 py-2 rounded-md font-medium hover:bg-blue-700 transition-colors"
                  >
                    설정 저장
                  </button>
                </div>
              </div>
            </div>
          )}

          <div className="mt-6 rounded-lg border border-gray-200 bg-gray-50 p-4">
            <p className="text-sm text-gray-700">
              결제 기능은 추후 도입 예정입니다. 현재는 무료 베타로 운영하며,
              서비스 유지를 위해 후원을 받고 있어요.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
