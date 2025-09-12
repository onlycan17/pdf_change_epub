import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileUpload, UsageIndicator } from '../components/common/index.ts'
import { useAuth } from '../hooks/useAuth'
import { Star, Zap, Shield, Clock, BookOpen, ArrowRight, Check, Upload } from 'lucide-react'

const Home: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isPremium, setIsPremium] = useState(false)
  const [dailyUsage, setDailyUsage] = useState(0)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (user) {
      setIsPremium(user.is_premium || false)
      setDailyUsage(2)
    }
    setIsLoading(false)
  }, [user])

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
    navigate('/upload', { state: { file } })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
        <div className="loading-spinner"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {/* Enhanced Hero Section - Desktop Optimized */}
      <section className="relative overflow-hidden bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-700">
        {/* Background Effects */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/5 via-purple-600/5 to-pink-600/5 dark:from-blue-500/10 dark:via-purple-500/10 dark:to-pink-500/10"></div>
        <div className="absolute inset-0">
          <div className="absolute top-10 left-10 w-96 h-96 bg-blue-500 rounded-full filter blur-3xl opacity-20 animate-pulse"></div>
          <div className="absolute bottom-10 right-10 w-96 h-96 bg-purple-500 rounded-full filter blur-3xl opacity-20 animate-pulse delay-1000"></div>
        </div>

        <div className="relative max-w-7xl mx-auto px-6 lg:px-12 py-24 lg:py-32">
          <div className="text-center max-w-5xl mx-auto animate-fade-in">
            {/* Badge */}
            <div className="mb-8 inline-flex items-center px-6 py-3 bg-white/80 dark:bg-slate-800/80 backdrop-blur rounded-full border border-blue-200 dark:border-blue-700">
              <Zap className="w-5 h-5 text-blue-600 dark:text-blue-400 mr-3" />
              <span className="text-lg font-semibold text-slate-900 dark:text-white">
                AI-Powered PDF to EPUB Conversion
              </span>
            </div>

            {/* Main Title */}
            <h1 className="text-5xl lg:text-7xl font-bold text-slate-900 dark:text-white mb-8 leading-tight">
              Transform PDFs into
              <span className="text-gradient-primary block mt-4 text-6xl lg:text-8xl relative">
                <span className="absolute inset-0 bg-gradient-to-r from-purple-500/20 via-blue-500/20 to-cyan-500/20 blur-xl rounded-full transform scale-110 -z-10"></span>
                Beautiful EPUBs
              </span>
            </h1>

            {/* Description */}
            <p className="text-xl lg:text-2xl text-slate-600 dark:text-slate-300 mb-12 max-w-3xl mx-auto leading-relaxed">
              Experience the future of document conversion with advanced AI-powered OCR, intelligent
              formatting preservation, and stunning design optimization.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-6 justify-center items-center mb-16">
              <button
                onClick={() =>
                  document.getElementById('upload-section')?.scrollIntoView({ behavior: 'smooth' })
                }
                className="btn btn-primary btn-xl group px-8 py-4 text-lg"
              >
                <Upload className="w-5 h-5 mr-3" />
                Start Converting
                <ArrowRight className="w-5 h-5 ml-3 group-hover:translate-x-1 transition-transform" />
              </button>

              <button
                onClick={() => navigate('/premium')}
                className="btn btn-outline btn-xl group px-8 py-4 text-lg"
              >
                <Star className="w-5 h-5 mr-3 group-hover:rotate-12 transition-transform" />
                Upgrade to Premium
              </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">10K+</div>
                <div className="text-slate-600 dark:text-slate-400">Active Users</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600 dark:text-green-400 mb-2">
                  99.9%
                </div>
                <div className="text-slate-600 dark:text-slate-400">Success Rate</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600 dark:text-purple-400 mb-2">
                  50K+
                </div>
                <div className="text-slate-600 dark:text-slate-400">Files Converted</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Enhanced Features Section */}
      <section className="py-24 lg:py-32 bg-white/80 dark:bg-slate-800/80 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="text-center mb-20">
            <h2 className="text-4xl lg:text-5xl font-bold text-slate-900 dark:text-white mb-6">
              Why Choose Our Converter?
            </h2>
            <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
              Advanced technology meets elegant design for the perfect conversion experience
            </p>
          </div>

          <div className="grid lg:grid-cols-4 gap-8">
            {[
              {
                icon: Zap,
                title: 'Lightning Fast',
                description: 'Convert documents in seconds with optimized processing',
                color: 'text-blue-500',
                gradient: 'from-blue-500 to-cyan-600',
              },
              {
                icon: Shield,
                title: 'Secure & Private',
                description: 'Your documents are processed securely and never stored',
                color: 'text-green-500',
                gradient: 'from-green-500 to-emerald-600',
              },
              {
                icon: BookOpen,
                title: 'Smart OCR',
                description: 'Advanced OCR technology for perfect text recognition',
                color: 'text-purple-500',
                gradient: 'from-purple-500 to-violet-600',
              },
              {
                icon: Clock,
                title: '24/7 Available',
                description: 'Convert documents anytime, anywhere you need',
                color: 'text-orange-500',
                gradient: 'from-orange-500 to-red-600',
              },
            ].map((feature, index) => (
              <div
                key={index}
                className="card hover-lift text-center group animate-slide-up"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="card-body p-8">
                  <div
                    className={`w-20 h-20 ${feature.color} bg-gradient-to-br ${feature.gradient}/20 rounded-3xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform`}
                  >
                    <feature.icon className="w-10 h-10" />
                  </div>
                  <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">
                    {feature.title}
                  </h3>
                  <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Enhanced Upload Section */}
      <section id="upload-section" className="py-24 lg:py-32">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="text-center mb-16">
            <h2 className="text-4xl lg:text-5xl font-bold text-slate-900 dark:text-white mb-6">
              Start Your Conversion
            </h2>
            <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
              Drop your PDF file here or click to browse. Experience seamless document
              transformation.
            </p>
          </div>

          <div className="max-w-4xl mx-auto">
            <div className="card hover-lift shadow-xl">
              <div className="card-body p-12 lg:p-16">
                <FileUpload
                  onFileSelect={handleFileSelect}
                  maxSize={isPremium ? 300 : 10}
                  className="mb-8"
                />

                {selectedFile && (
                  <div className="text-center mt-8">
                    <button
                      onClick={() => handleFileSelect(selectedFile)}
                      className="btn btn-primary btn-xl group px-10 py-4 text-lg"
                    >
                      Convert Now
                      <ArrowRight className="w-5 h-5 ml-3 group-hover:translate-x-1 transition-transform" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Quick Features */}
          <div className="mt-20 grid lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <div className="text-center p-6 bg-slate-50 dark:bg-slate-800 rounded-xl">
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center mx-auto mb-4">
                <BookOpen className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="font-semibold text-slate-900 dark:text-white mb-2">
                Format Preservation
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Maintain original formatting and layout
              </p>
            </div>

            <div className="text-center p-6 bg-slate-50 dark:bg-slate-800 rounded-xl">
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Zap className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="font-semibold text-slate-900 dark:text-white mb-2">
                Instant Processing
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Lightning-fast conversion speed
              </p>
            </div>

            <div className="text-center p-6 bg-slate-50 dark:bg-slate-800 rounded-xl">
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Shield className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="font-semibold text-slate-900 dark:text-white mb-2">
                Secure Processing
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Your files are safe and private
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Enhanced Pricing Section */}
      <section className="py-24 lg:py-32 bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-800 dark:to-slate-700">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="text-center mb-20">
            <h2 className="text-4xl lg:text-5xl font-bold text-slate-900 dark:text-white mb-6">
              Choose Your Plan
            </h2>
            <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
              Start free and upgrade when you need more power and advanced features
            </p>
          </div>

          <div className="max-w-5xl mx-auto">
            <div className="grid lg:grid-cols-2 gap-12">
              {/* Free Plan */}
              <div className="card hover-lift shadow-lg">
                <div className="card-body p-10">
                  <div className="text-center mb-8">
                    <h3 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">Free</h3>
                    <div className="text-5xl font-bold text-slate-900 dark:text-white mb-2">
                      $0<span className="text-lg font-normal">/month</span>
                    </div>
                    <p className="text-slate-600 dark:text-slate-400">Perfect for casual users</p>
                  </div>

                  <ul className="space-y-4 mb-10">
                    {[
                      'Up to 10MB files',
                      'Basic OCR text extraction',
                      'Standard email support',
                      '5 conversions per day',
                      'Web-based reading',
                    ].map((feature, index) => (
                      <li
                        key={index}
                        className="flex items-center text-slate-600 dark:text-slate-300"
                      >
                        <Check className="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>

                  <button className="btn btn-secondary btn-lg w-full">Current Plan</button>
                </div>
              </div>

              {/* Premium Plan */}
              <div className="card hover-lift relative shadow-xl border-2 border-gradient-primary transform scale-105">
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="badge badge-premium px-4 py-2 text-sm font-semibold">
                    Most Popular
                  </span>
                </div>

                <div className="card-body p-10">
                  <div className="text-center mb-8">
                    <h3 className="text-3xl font-bold text-gradient-primary mb-4">Premium</h3>
                    <div className="text-5xl font-bold text-slate-900 dark:text-white mb-2">
                      $9.99<span className="text-lg font-normal">/month</span>
                    </div>
                    <p className="text-slate-600 dark:text-slate-400">
                      Advanced features for professionals
                    </p>
                  </div>

                  <ul className="space-y-4 mb-10">
                    {[
                      'Up to 300MB files',
                      'Advanced OCR (Korean/English)',
                      'Priority email support',
                      'Unlimited conversions',
                      'High-resolution images',
                      'No advertisements',
                      'EPUB customization',
                      'Mobile app access',
                    ].map((feature, index) => (
                      <li
                        key={index}
                        className="flex items-center text-slate-600 dark:text-slate-300"
                      >
                        <Check className="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>

                  <button
                    onClick={() => navigate('/premium')}
                    className="btn btn-primary btn-lg w-full group"
                  >
                    Upgrade to Premium
                    <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Usage Section (Free Users Only) */}
      {!isPremium && (
        <section className="py-24 lg:py-32 bg-white/80 dark:bg-slate-800/80 backdrop-blur">
          <div className="max-w-4xl mx-auto px-6 lg:px-12">
            <div className="card shadow-lg">
              <div className="card-body p-10 text-center">
                <h3 className="text-2xl lg:text-3xl font-bold text-slate-900 dark:text-white mb-8">
                  Daily Usage Tracker
                </h3>

                <div className="mb-8">
                  <UsageIndicator dailyUsage={dailyUsage} dailyLimit={5} isPremium={isPremium} />
                </div>

                <p className="text-lg text-slate-600 dark:text-slate-300 mb-8">
                  You've used {dailyUsage} of your 5 daily conversions
                </p>

                <button onClick={() => navigate('/premium')} className="btn btn-accent btn-lg">
                  Upgrade for Unlimited Usage
                </button>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Enhanced CTA Section */}
      <section className="py-24 lg:py-32 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600">
        <div className="max-w-4xl mx-auto px-6 lg:px-12 text-center">
          <h2 className="text-4xl lg:text-5xl font-bold text-white mb-8">
            Ready to Transform Your Documents?
          </h2>
          <p className="text-xl text-white/90 mb-12 leading-relaxed">
            Join thousands of satisfied users who trust our AI-powered conversion technology to
            transform their PDF documents into beautiful, readable EPUBs.
          </p>

          <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
            <button
              onClick={() =>
                document.getElementById('upload-section')?.scrollIntoView({ behavior: 'smooth' })
              }
              className="btn btn-secondary btn-xl px-8 py-4 text-lg bg-white text-blue-600 hover:bg-white/90"
            >
              Get Started Free
            </button>

            <button
              onClick={() => navigate('/premium')}
              className="btn btn-outline btn-xl px-8 py-4 text-lg border-white text-white hover:bg-white/10"
            >
              View Premium Features
            </button>
          </div>

          <div className="mt-12 text-white/70">No credit card required • Free to start</div>
        </div>
      </section>
    </div>
  )
}

export default Home
