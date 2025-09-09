import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileUpload, UsageIndicator } from '../components/common/index.ts'
import { useAuth } from '../hooks/useAuth'
import { Star, Zap, Shield, Clock, BookOpen, ArrowRight, Check } from 'lucide-react'

const Home: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isPremium, setIsPremium] = useState(false)
  const [dailyUsage, setDailyUsage] = useState(0)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (user) {
      setIsPremium(false)
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 opacity-10 dark:opacity-20"></div>
        <div className="absolute inset-0">
          <div className="absolute top-0 left-0 w-96 h-96 bg-blue-500 rounded-full filter blur-3xl opacity-20 animate-pulse"></div>
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-purple-500 rounded-full filter blur-3xl opacity-20 animate-pulse delay-1000"></div>
        </div>

        <div className="relative container mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 lg:pt-32 lg:pb-24">
          <div className="text-center max-w-4xl mx-auto">
            <div className="mb-6">
              <span className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white text-sm font-medium rounded-full">
                <Zap className="w-4 h-4 mr-2" />
                AI-Powered Conversion
              </span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold text-slate-900 dark:text-white mb-6 leading-tight">
              Transform PDFs into
              <span className="text-gradient-primary block mt-2">Beautiful EPUBs</span>
            </h1>

            <p className="text-xl lg:text-2xl text-slate-600 dark:text-slate-300 mb-8 max-w-2xl mx-auto leading-relaxed">
              Experience the future of document conversion with AI-powered OCR, intelligent
              formatting, and stunning design preservation.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <button
                onClick={() =>
                  document.getElementById('upload-section')?.scrollIntoView({ behavior: 'smooth' })
                }
                className="btn btn-primary btn-lg group"
              >
                Start Converting
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>

              <button onClick={() => navigate('/premium')} className="btn btn-outline btn-lg group">
                <Star className="w-5 h-5 group-hover:rotate-12 transition-transform" />
                Upgrade to Premium
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 lg:py-24 bg-white/50 dark:bg-slate-800/50 backdrop-blur">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12 lg:mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-slate-900 dark:text-white mb-4">
              Why Choose Our Converter?
            </h2>
            <p className="text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto">
              Advanced technology meets elegant design for the perfect conversion experience
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8">
            {[
              {
                icon: Zap,
                title: 'Lightning Fast',
                description: 'Convert documents in seconds with optimized processing',
                color: 'text-blue-500',
              },
              {
                icon: Shield,
                title: 'Secure & Private',
                description: 'Your documents are processed securely and never stored',
                color: 'text-green-500',
              },
              {
                icon: BookOpen,
                title: 'Smart OCR',
                description: 'Advanced OCR technology for perfect text recognition',
                color: 'text-purple-500',
              },
              {
                icon: Clock,
                title: '24/7 Available',
                description: 'Convert documents anytime, anywhere you need',
                color: 'text-orange-500',
              },
            ].map((feature, index) => (
              <div key={index} className="card hover-lift text-center group">
                <div className="card-body">
                  <div
                    className={`w-16 h-16 ${feature.color} bg-gradient-to-br from-current/20 to-current/10 rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform`}
                  >
                    <feature.icon className="w-8 h-8" />
                  </div>
                  <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-slate-600 dark:text-slate-300">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Upload Section */}
      <section id="upload-section" className="py-16 lg:py-24">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl lg:text-4xl font-bold text-slate-900 dark:text-white mb-4">
                Start Your Conversion
              </h2>
              <p className="text-lg text-slate-600 dark:text-slate-300">
                Drop your PDF file here or click to browse
              </p>
            </div>

            <div className="card hover-lift">
              <div className="card-body p-8 lg:p-12">
                <FileUpload
                  onFileSelect={handleFileSelect}
                  maxSize={isPremium ? 300 : 10}
                  className="mb-6"
                />

                {selectedFile && (
                  <div className="text-center mt-6">
                    <button
                      onClick={() => handleFileSelect(selectedFile)}
                      className="btn btn-primary btn-lg group"
                    >
                      Convert Now
                      <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-16 lg:py-24 bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-800 dark:to-slate-700">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12 lg:mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-slate-900 dark:text-white mb-4">
              Choose Your Plan
            </h2>
            <p className="text-lg text-slate-600 dark:text-slate-300">
              Start free and upgrade when you need more power
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 lg:gap-12 max-w-5xl mx-auto">
            {/* Free Plan */}
            <div className="card hover-lift">
              <div className="card-body p-8">
                <div className="text-center mb-6">
                  <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Free</h3>
                  <div className="text-4xl font-bold text-slate-900 dark:text-white mb-1">$0</div>
                  <p className="text-slate-600 dark:text-slate-300">Perfect for casual users</p>
                </div>

                <ul className="space-y-3 mb-8">
                  {[
                    'Up to 10MB files',
                    'Basic OCR',
                    'Standard support',
                    '5 conversions per day',
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

                <button className="btn btn-secondary btn-block">Current Plan</button>
              </div>
            </div>

            {/* Premium Plan */}
            <div className="card hover-lift relative border-2 border-gradient-primary">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                  Most Popular
                </span>
              </div>

              <div className="card-body p-8">
                <div className="text-center mb-6">
                  <h3 className="text-2xl font-bold text-gradient-primary mb-2">Premium</h3>
                  <div className="text-4xl font-bold text-slate-900 dark:text-white mb-1">
                    $9.99
                  </div>
                  <p className="text-slate-600 dark:text-slate-300">per month</p>
                </div>

                <ul className="space-y-3 mb-8">
                  {[
                    'Up to 300MB files',
                    'Advanced OCR (Korean/English)',
                    'Priority support',
                    'Unlimited conversions',
                    'High-resolution images',
                    'No ads',
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
                  className="btn btn-primary btn-block group"
                >
                  Upgrade to Premium
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Usage Section */}
      {!isPremium && (
        <section className="py-16 lg:py-24 bg-white/30 dark:bg-slate-800/30 backdrop-blur">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8">
            <div className="max-w-2xl mx-auto">
              <div className="card">
                <div className="card-body p-8">
                  <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 text-center">
                    Daily Usage
                  </h3>
                  <UsageIndicator dailyUsage={dailyUsage} dailyLimit={5} isPremium={isPremium} />
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* CTA Section */}
      <section className="py-16 lg:py-24 bg-gradient-to-r from-blue-600 to-purple-600">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">
            Ready to Transform Your Documents?
          </h2>
          <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
            Join thousands of users who trust our AI-powered conversion technology
          </p>
          <button
            onClick={() =>
              document.getElementById('upload-section')?.scrollIntoView({ behavior: 'smooth' })
            }
            className="btn btn-secondary btn-lg bg-white text-blue-600 hover:bg-white/90"
          >
            Get Started Now
          </button>
        </div>
      </section>
    </div>
  )
}

export default Home
