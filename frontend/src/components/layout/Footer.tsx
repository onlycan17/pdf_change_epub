import React from 'react';
import { Link } from 'react-router-dom';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white border-t border-gray-200">
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Company Info */}
          <div className="md:col-span-2">
            <Link to="/" className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">P2E</span>
              </div>
              <span className="text-xl font-bold text-gray-900">
                PDF to EPUB
              </span>
            </Link>
            <p className="text-gray-600 mb-4 max-w-md">
              고품질 PDF를 EPUB으로 변환하는 최고의 솔루션입니다. AI 기술을
              활용하여 정확한 텍스트 추출과 최적의 레이아웃을 제공합니다.
            </p>
            <p className="text-sm leading-7 text-gray-500">
              서비스 안내, 도움말, 정책 문서를 통해 운영 방식과 이용 조건을
              공개적으로 확인할 수 있습니다.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">
              빠른 링크
            </h3>
            <ul className="space-y-2">
              <li>
                <Link to="/" className="text-gray-600 hover:text-blue-600">
                  홈
                </Link>
              </li>
              <li>
                <Link
                  to="/upload"
                  className="text-gray-600 hover:text-blue-600"
                >
                  변환하기
                </Link>
              </li>
              <li>
                <Link
                  to="/support"
                  className="text-gray-600 hover:text-blue-600"
                >
                  운영 안내
                </Link>
              </li>
              <li>
                <Link
                  to="/service-guide"
                  className="text-gray-600 hover:text-blue-600"
                >
                  서비스 안내
                </Link>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">
              지원
            </h3>
            <ul className="space-y-2">
              <li>
                <Link
                  to="/help-center"
                  className="text-gray-600 hover:text-blue-600"
                >
                  도움말 센터
                </Link>
              </li>
              <li>
                <Link
                  to="/large-file-request"
                  className="text-gray-600 hover:text-blue-600"
                >
                  대용량 요청
                </Link>
              </li>
              <li>
                <Link
                  to="/contact"
                  className="text-gray-600 hover:text-blue-600"
                >
                  문의하기
                </Link>
              </li>
              <li>
                <Link to="/terms" className="text-gray-600 hover:text-blue-600">
                  이용약관
                </Link>
              </li>
              <li>
                <Link
                  to="/privacy"
                  className="text-gray-600 hover:text-blue-600"
                >
                  개인정보처리방침
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-8 pt-8 border-t border-gray-200">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-500 text-sm">
              © {currentYear} PDF to EPUB Converter. All rights reserved.
            </p>
            <div className="mt-4 md:mt-0 flex space-x-6 text-sm text-gray-500">
              <Link to="/service-guide" className="hover:text-blue-600">
                서비스 안내
              </Link>
              <Link to="/terms" className="hover:text-blue-600">
                이용약관
              </Link>
              <Link to="/privacy" className="hover:text-blue-600">
                개인정보처리방침
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
