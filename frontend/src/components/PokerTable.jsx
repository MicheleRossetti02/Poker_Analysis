import { useState } from 'react';
import { User, Crown, Zap } from 'lucide-react';
import Card from './Card';
import CardSelectorModal from './CardSelectorModal';
import Advisor from './Advisor';
import { analyzeSpot } from '../services/api';

/**
 * Position configuration for 6-max table
 * Positions are placed around the oval table
 */
const POSITIONS = [
    { id: 'BTN', label: 'BTN', angle: 270, isHero: true },
    { id: 'SB', label: 'SB', angle: 210 },
    { id: 'BB', label: 'BB', angle: 150 },
    { id: 'UTG', label: 'UTG', angle: 90 },
    { id: 'MP', label: 'MP', angle: 30 },
    { id: 'CO', label: 'CO', angle: 330 },
];

const STACK_SIZES = [100, 50, 20];

/**
 * PokerTable Component
 * Main poker table visualization with seat positions
 */
export default function PokerTable() {
    const [heroCards, setHeroCards] = useState([]);
    const [heroPosition, setHeroPosition] = useState('BTN');
    const [villainPosition, setVillainPosition] = useState('BB');
    const [stackSize, setStackSize] = useState(100);
    const [showCardSelector, setShowCardSelector] = useState(false);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleAnalyze = async () => {
        if (heroCards.length !== 2) {
            setError('Please select 2 cards');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await analyzeSpot({
                hero_position: heroPosition,
                villain_position: villainPosition,
                stack: stackSize,
                hand: heroCards,
            });
            setResult(response);
        } catch (err) {
            setError(err.response?.data?.detail || 'Analysis failed');
            console.error('API Error:', err);
        } finally {
            setLoading(false);
        }
    };

    // Calculate seat position on the oval
    const getSeatPosition = (angle) => {
        const radiusX = 42; // % of container width
        const radiusY = 38; // % of container height
        const rad = (angle * Math.PI) / 180;
        return {
            left: `${50 + radiusX * Math.cos(rad)}%`,
            top: `${50 + radiusY * Math.sin(rad)}%`,
        };
    };

    return (
        <div className="min-h-screen flex flex-col items-center justify-center p-4">
            {/* Header */}
            <header className="text-center mb-8">
                <h1 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
                    <Crown className="w-10 h-10 text-yellow-400" />
                    Poker Advisor
                </h1>
                <p className="text-gray-400">Select your cards and get GTO recommendations</p>
            </header>

            {/* Controls Bar */}
            <div className="flex flex-wrap items-center justify-center gap-4 mb-6 p-4 bg-gray-800/50 rounded-xl backdrop-blur-sm">
                {/* Hero Position */}
                <div>
                    <label className="block text-xs text-gray-400 mb-1">Hero Position</label>
                    <select
                        value={heroPosition}
                        onChange={(e) => setHeroPosition(e.target.value)}
                        className="bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600 focus:border-yellow-400 focus:outline-none"
                    >
                        {POSITIONS.map(p => (
                            <option key={p.id} value={p.id}>{p.id}</option>
                        ))}
                    </select>
                </div>

                {/* Villain Position */}
                <div>
                    <label className="block text-xs text-gray-400 mb-1">Villain Position</label>
                    <select
                        value={villainPosition}
                        onChange={(e) => setVillainPosition(e.target.value)}
                        className="bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600 focus:border-yellow-400 focus:outline-none"
                    >
                        {POSITIONS.filter(p => p.id !== heroPosition).map(p => (
                            <option key={p.id} value={p.id}>{p.id}</option>
                        ))}
                    </select>
                </div>

                {/* Stack Size */}
                <div>
                    <label className="block text-xs text-gray-400 mb-1">Stack Size</label>
                    <div className="flex gap-1">
                        {STACK_SIZES.map(size => (
                            <button
                                key={size}
                                onClick={() => setStackSize(size)}
                                className={`px-3 py-2 rounded-lg font-medium transition-colors ${stackSize === size
                                        ? 'bg-yellow-500 text-gray-900'
                                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                    }`}
                            >
                                {size}bb
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Main Table Area */}
            <div className="relative w-full max-w-4xl aspect-[16/10]">
                {/* Poker Table (Green Oval) */}
                <div className="absolute inset-8 rounded-[50%] bg-gradient-to-br from-emerald-800 to-green-900 shadow-2xl border-8 border-amber-900">
                    {/* Table felt texture overlay */}
                    <div className="absolute inset-0 rounded-[50%] bg-[radial-gradient(ellipse_at_center,_transparent_0%,_rgba(0,0,0,0.3)_100%)]"></div>

                    {/* Table rail */}
                    <div className="absolute -inset-2 rounded-[50%] border-4 border-amber-800 pointer-events-none"></div>

                    {/* Center content - Analyze button & Advisor */}
                    <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 p-8">
                        {/* Advisor Result */}
                        <div className="w-full max-w-xs">
                            <Advisor result={result} loading={loading} />
                        </div>

                        {/* Error display */}
                        {error && (
                            <div className="bg-red-900/80 text-red-200 px-4 py-2 rounded-lg text-sm">
                                {error}
                            </div>
                        )}

                        {/* Analyze Button */}
                        <button
                            onClick={handleAnalyze}
                            disabled={heroCards.length !== 2 || loading}
                            className={`
                px-8 py-4 rounded-xl font-bold text-lg shadow-lg
                transition-all duration-300 transform
                flex items-center gap-2
                ${heroCards.length === 2 && !loading
                                    ? 'bg-gradient-to-r from-yellow-500 to-amber-500 text-gray-900 hover:scale-105 hover:shadow-yellow-500/30'
                                    : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                                }
              `}
                        >
                            <Zap className="w-5 h-5" />
                            {loading ? 'Analyzing...' : 'ANALYZE HAND'}
                        </button>
                    </div>
                </div>

                {/* Seat Positions */}
                {POSITIONS.map(pos => {
                    const position = getSeatPosition(pos.angle);
                    const isHeroSeat = pos.id === heroPosition;

                    return (
                        <div
                            key={pos.id}
                            className="absolute transform -translate-x-1/2 -translate-y-1/2"
                            style={position}
                        >
                            {/* Seat circle */}
                            <div
                                className={`
                  w-20 h-20 rounded-full flex flex-col items-center justify-center
                  transition-all duration-300 cursor-pointer
                  ${isHeroSeat
                                        ? 'bg-gradient-to-br from-yellow-600 to-amber-700 ring-4 ring-yellow-400 shadow-lg shadow-yellow-500/30'
                                        : 'bg-gray-800 hover:bg-gray-700 border-2 border-gray-600'
                                    }
                `}
                                onClick={isHeroSeat ? () => setShowCardSelector(true) : undefined}
                            >
                                {/* Position label */}
                                <span className={`text-xs font-bold ${isHeroSeat ? 'text-yellow-100' : 'text-gray-400'}`}>
                                    {pos.id}
                                </span>

                                {/* Cards or User icon */}
                                {isHeroSeat && heroCards.length > 0 ? (
                                    <div className="flex -space-x-2 mt-1">
                                        {heroCards.map(card => (
                                            <Card key={card} card={card} small />
                                        ))}
                                    </div>
                                ) : (
                                    <User className={`w-6 h-6 ${isHeroSeat ? 'text-yellow-200' : 'text-gray-500'}`} />
                                )}
                            </div>

                            {/* Hero label */}
                            {isHeroSeat && (
                                <div className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 text-yellow-400 font-bold text-sm">
                                    HERO
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Card Selector Modal */}
            <CardSelectorModal
                isOpen={showCardSelector}
                onClose={() => setShowCardSelector(false)}
                onSelect={setHeroCards}
                selectedCards={heroCards}
                maxCards={2}
            />

            {/* Footer hint */}
            <p className="text-gray-500 text-sm mt-8">
                Click on your seat to select hole cards
            </p>
        </div>
    );
}
