
import { useNavigate, useLocation } from 'react-router-dom';
import { AppCard } from './AppCard';
import { AppButton } from './AppButton';

export function PlaceholderPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const featureName = location.pathname.split('/').filter(Boolean).map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ');

    return (
        <div className="min-h-screen bg-neutral-950 flex items-center justify-center p-6">
            <div className="aurora-bg" />

            <AppCard variant="glass" padding="lg" className="max-w-md w-full text-center relative z-10">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center mx-auto mb-6">
                    <svg className="w-8 h-8 text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                    </svg>
                </div>

                <h1 className="text-2xl font-bold text-white mb-2">{featureName || 'Coming Soon'}</h1>
                <p className="text-white/60 mb-8">
                    This feature is currently under development. Check back soon for updates!
                </p>

                <AppButton variant="outline" onClick={() => navigate('/dashboard')} className="w-full">
                    Back to Dashboard
                </AppButton>
            </AppCard>
        </div>
    );
}
