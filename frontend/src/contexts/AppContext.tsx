import React, { createContext, useContext, useReducer, ReactNode } from 'react'
import { User, ConversionJob, Notification } from '@/types'

interface AppState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  conversionJobs: ConversionJob[]
  notifications: Notification[]
}

type AppAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_USER'; payload: User | null }
  | { type: 'SET_AUTHENTICATED'; payload: boolean }
  | { type: 'ADD_CONVERSION_JOB'; payload: ConversionJob }
  | { type: 'UPDATE_CONVERSION_JOB'; payload: ConversionJob }
  | { type: 'REMOVE_CONVERSION_JOB'; payload: string }
  | { type: 'ADD_NOTIFICATION'; payload: Notification }
  | { type: 'REMOVE_NOTIFICATION'; payload: string }

interface AppContextType {
  state: AppState
  dispatch: React.Dispatch<AppAction>
}

const initialState: AppState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  conversionJobs: [],
  notifications: [],
}

const appReducer = (state: AppState, action: AppAction): AppState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload }
    case 'SET_USER':
      return { ...state, user: action.payload }
    case 'SET_AUTHENTICATED':
      return { ...state, isAuthenticated: action.payload }
    case 'ADD_CONVERSION_JOB':
      return {
        ...state,
        conversionJobs: [...state.conversionJobs, action.payload],
      }
    case 'UPDATE_CONVERSION_JOB':
      return {
        ...state,
        conversionJobs: state.conversionJobs.map(job =>
          job.id === action.payload.id ? action.payload : job
        ),
      }
    case 'REMOVE_CONVERSION_JOB':
      return {
        ...state,
        conversionJobs: state.conversionJobs.filter(job => job.id !== action.payload),
      }
    case 'ADD_NOTIFICATION':
      return {
        ...state,
        notifications: [...state.notifications, action.payload],
      }
    case 'REMOVE_NOTIFICATION':
      return {
        ...state,
        notifications: state.notifications.filter(notification => notification.id !== action.payload),
      }
    default:
      return state
  }
}

const AppContext = createContext<AppContextType | undefined>(undefined)

interface AppProviderProps {
  children: ReactNode
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState)

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  )
}

export const useApp = (): AppContextType => {
  const context = useContext(AppContext)
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider')
  }
  return context
}