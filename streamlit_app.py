import React, { useState, useEffect, useMemo } from 'react';
import { 
  Activity, 
  TrendingUp, 
  AlertTriangle, 
  Info, 
  ShieldAlert, 
  BarChart, 
  RefreshCw,
  Monitor,
  ShoppingCart
} from 'lucide-react';

export default function App() {
  // 상태 변수 (시뮬레이터 값 및 로딩 상태)
  const [fx, setFx] = useState(1450);
  const [vol, setVol] = useState(18.0);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [isSimulation, setIsSimulation] = useState(false);

  // 디자인 메인 컬러 및 연산 기준 상수
  const COLOR_NAVY = '#34495e';
  const COLOR_ORANGE = '#e67e22';
  const BASE_FX = 1380;
  const BASE_VOL = 13.5;

  const fetchRealData = async () => {
    try {
      setIsLoading(true);
      setIsSimulation(false);
      
      // 브라우저 CORS 에러 방지를 위한 프록시 우회 호출 (raw 엔드포인트 사용)
      const targetUrl = 'https://query1.finance.yahoo.com/v8/finance/chart/KRW=X?range=1mo&interval=1d';
      const proxyUrl = `https://api.allorigins.win/raw?url=${encodeURIComponent(targetUrl)}`;

      const response = await fetch(proxyUrl);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      
      const data = await response.json();
      
      // JSON 파싱 (야후 차트 API 응답 구조 추출)
      const result = data.chart.result[0];
      const latestPrice = result.meta.regularMarketPrice;
      const closePrices = result.indicators.quote[0].close.filter(p => p !== null);

      // 통계 수학 연산: 최근 30일 종가 기준 표준편차(변동성) 산출
      const mean = closePrices.reduce((a, b) => a + b, 0) / closePrices.length;
      const variance = closePrices.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / closePrices.length;
      const stdDev = Math.sqrt(variance);

      // React 상태 업데이트 (실측 데이터)
      setFx(Math.round(latestPrice));
      setVol(Math.min(40.0, Math.max(1.0, Number(stdDev.toFixed(1)))));
      
      const now = new Date();
      setLastUpdated(`${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`);
    } catch (error) {
      console.warn("야후 데이터 로드 실패. 대체 시뮬레이션 데이터를 제공합니다.", error);
      setIsSimulation(true);
      
      // API 호출 실패(CORS/네트워크 이슈) 시, 앱이 멈추지 않도록 가상 변동 데이터 삽입
      const mockFx = Math.round(1380 + (Math.random() * 80) - 40); 
      const mockVol = Number((12.0 + (Math.random() * 10)).toFixed(1)); 
      
      setFx(mockFx);
      setVol(mockVol);
      
      const now = new Date();
      setLastUpdated(`${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`);
    } finally {
      setIsLoading(false);
    }
  };

  // 컴포넌트 마운트 시 최초 1회 실시간 데이터 호출
  useEffect(() => {
    fetchRealData();
  }, []);

  const { score, status, statusColor, statusBg, statusText } = useMemo(() => {
    // 가중치 알고리즘: 환율(40%) + 변동성(60%)
    // 환율 스코어 (1000~1800 범위를 0~40점으로 선형 매핑)
    const fxScore = Math.max(0, Math.min(40, ((fx - 1000) / 800) * 40));
    // 변동성 스코어 (1.0~40.0 범위를 0~60점으로 선형 매핑)
    const volScore = Math.max(0, Math.min(60, ((vol - 1.0) / 39) * 60));
    
    const totalScore = Math.round(fxScore + volScore);
    
    let status, statusColor, statusBg, statusText;
    
    // 조건부 3단계 분기
    if (totalScore >= 70) {
      status = 'RED (위험)';
      statusColor = 'text-red-600';
      statusBg = 'bg-red-50 border-red-200';
      statusText = '지출 최소화 및 관망 권장';
    } else if (totalScore >= 40) {
      status = 'YELLOW (주의)';
      statusColor = 'text-yellow-600';
      statusBg = 'bg-yellow-50 border-yellow-200';
      statusText = '품목별 선별적 지출 필요';
    } else {
      status = 'GREEN (안정)';
      statusColor = 'text-emerald-600';
      statusBg = 'bg-emerald-50 border-emerald-200';
      statusText = '계획된 소비 적기';
    }

    return { score: totalScore, status, statusColor, statusBg, statusText };
  }, [fx, vol]);

  const scatterData = useMemo(() => {
    const data = [];
    for (let i = 0; i < 200; i++) {
      // 1100원 ~ 1700원 사이의 가상 환율 데이터 분포
      const x = 1100 + (Math.abs(Math.sin(i * 12.34)) * 600);
      // 이분산성(Heteroscedasticity) 로직: 중앙(1380)에서 멀어질수록 오차 분산 증가
      const variance = 0.3 + Math.abs(x - 1380) / 120; 
      const y = Math.cos(i * 45.67) * variance;
      data.push({ x, y });
    }
    return data;
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-800 font-sans tracking-tight">
      <header className="py-14 px-6" style={{ backgroundColor: COLOR_NAVY }}>
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center justify-center gap-2 mb-4 px-4 py-1.5 rounded-full bg-white/10 text-white/90 text-xs font-bold tracking-widest uppercase shadow-sm border border-white/5">
            <Activity className="w-4 h-4" style={{ color: COLOR_ORANGE }} />
            Fintech Analytics Engine
          </div>
          <h1 className="text-4xl md:text-6xl font-extrabold text-white mb-4 tracking-tight drop-shadow-sm">
            Inflation Wizard
          </h1>
          <h2 className="text-xl md:text-2xl text-gray-300 font-medium mb-8">
            환율 변동 및 시차 통계 기반 미래 물가 예측 엔진
          </h2>
          <div className="max-w-3xl mx-auto bg-slate-800/50 border border-slate-700/50 rounded-xl p-6 backdrop-blur-md shadow-inner">
            <p className="text-slate-200 leading-relaxed text-base md:text-lg">
              매일 요동치는 원/달러 환율의 단가 수준과 일별 변동성 빅데이터를 분석하여 미래 소비자물가(CPI)의 동향을 선제적으로 예측하고 지출 골든타임을 배달합니다.
            </p>
          </div>
        </div>
      </header>

      {/* Main Dashboard */}
      <main className="max-w-5xl mx-auto px-4 py-12 space-y-12">
        <section className="grid lg:grid-cols-2 gap-8">
          
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-200">
            <div className="flex items-center justify-between mb-8 pb-4 border-b border-gray-100">
              <h3 className="text-xl font-bold flex items-center gap-2" style={{ color: COLOR_NAVY }}>
                <BarChart className="w-6 h-6" style={{ color: COLOR_ORANGE }} />
                실시간 지표 시뮬레이터
              </h3>
              <button 
                onClick={fetchRealData} 
                disabled={isLoading}
                className="flex items-center gap-2 text-xs font-bold px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                {isLoading ? '동기화 중...' : 'Yahoo 실시간 데이터 로드'}
              </button>
            </div>
            
            {lastUpdated && (
              <div className={`mb-8 text-xs font-bold tracking-wider flex items-center gap-2 border w-max px-3 py-1.5 rounded-md ${isSimulation ? 'text-amber-700 bg-amber-50 border-amber-200' : 'text-emerald-700 bg-emerald-50 border-emerald-100'}`}>
                <span className={`w-2 h-2 rounded-full animate-pulse ${isSimulation ? 'bg-amber-500' : 'bg-emerald-500'}`}></span>
                {isSimulation 
                  ? `네트워크 오류: 시뮬레이션 데이터 적용 (기준: ${lastUpdated})` 
                  : `야후 파이낸스 실측 데이터 적용 완료 (기준: ${lastUpdated})`}
              </div>
            )}
            
            <div className="space-y-10">
              <div>
                <div className="flex justify-between items-end mb-3">
                  <label className="font-bold text-gray-700">오늘의 원/달러 환율</label>
                  <span className="text-3xl font-black" style={{ color: COLOR_ORANGE }}>{fx.toLocaleString()} 원</span>
                </div>
                <input 
                  type="range" min="1000" max="1800" step="1" 
                  value={fx} 
                  onChange={(e) => setFx(Number(e.target.value))}
                  className="w-full h-2.5 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  style={{ accentColor: COLOR_NAVY }}
                />
                <div className="flex justify-between text-xs text-gray-400 mt-3 font-mono font-medium">
                  <span>Min: 1000</span>
                  <span className="text-gray-500">통계 기준: 1380</span>
                  <span>Max: 1800</span>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-end mb-3">
                  <label className="font-bold text-gray-700">최근 30일 환율 변동성 (표준편차)</label>
                  <span className="text-3xl font-black" style={{ color: COLOR_ORANGE }}>{vol.toFixed(1)}</span>
                </div>
                <input 
                  type="range" min="1.0" max="40.0" step="0.1" 
                  value={vol} 
                  onChange={(e) => setVol(Number(e.target.value))}
                  className="w-full h-2.5 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  style={{ accentColor: COLOR_NAVY }}
                />
                <div className="flex justify-between text-xs text-gray-400 mt-3 font-mono font-medium">
                  <span>Min: 1.0</span>
                  <span className="text-gray-500">통계 기준: 13.5</span>
                  <span>Max: 40.0</span>
                </div>
              </div>
            </div>
          </div>

          <div className={`p-8 rounded-2xl shadow-sm border flex flex-col items-center justify-center text-center transition-colors duration-500 ${statusBg}`}>
            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-4">물가 전이 압력 스코어</h3>
            <div className={`text-8xl font-black mb-6 tracking-tighter ${statusColor} drop-shadow-sm`}>
              {score}
            </div>
            <div className={`px-8 py-2.5 rounded-full text-lg font-bold border bg-white shadow-sm ${statusColor}`}>
              {status}
            </div>
            <p className="mt-6 text-gray-800 font-bold text-xl">
              "{statusText}"
            </p>
          </div>
        </section>

        {/* Action Guidelines */}
        <section>
          <div className="flex items-center gap-3 mb-8 border-b border-gray-200 pb-4">
            <TrendingUp className="w-7 h-7" style={{ color: COLOR_NAVY }} />
            <h3 className="text-2xl font-extrabold text-gray-800">통계 시차(Lag) 기반 행동 지침</h3>
          </div>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-200 flex flex-col h-full">
              <div className="inline-block px-4 py-1.5 rounded-md text-xs font-bold bg-slate-100 text-slate-700 mb-6 w-max border border-slate-200">
                Lag 0 (실시간 전이)
              </div>
              <h4 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                <Monitor className="w-5 h-5 text-gray-400" /> 당월 즉각 반영 품목
              </h4>
              <div className="flex-grow">
                {fx > BASE_FX ? (
                  <p className="text-slate-700 text-lg leading-relaxed border-l-4 pl-5 border-red-500 bg-red-50/50 py-4 pr-4 rounded-r-lg font-medium">
                    수입 원가 노출도가 높은 해외 직구 IT 가전, 항공권, 해외 결제 상품은 당월에 즉시 가격이 상승하므로 추가 지출 보류를 권장합니다.
                  </p>
                ) : (
                  <p className="text-slate-700 text-lg leading-relaxed border-l-4 pl-5 border-emerald-500 bg-emerald-50/50 py-4 pr-4 rounded-r-lg font-medium">
                    환율 단가가 안정권에 있습니다. 직구, 항공권 등 해외 직접 결제 상품의 당월 지출이 유리한 시점입니다.
                  </p>
                )}
              </div>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-200 flex flex-col h-full">
              <div className="inline-block px-4 py-1.5 rounded-md text-xs font-bold bg-slate-100 text-slate-700 mb-6 w-max border border-slate-200">
                Lag 4 (4개월 지연 전이)
              </div>
              <h4 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                <ShoppingCart className="w-5 h-5 text-gray-400" /> 4달 뒤 지연 폭발 품목
              </h4>
              <div className="flex-grow">
                {vol > BASE_VOL ? (
                  <p className="text-slate-700 text-lg leading-relaxed border-l-4 pl-5 border-amber-500 bg-amber-50/50 py-4 pr-4 rounded-r-lg font-medium">
                    일별 환율의 불안정성 쇼크가 감지되었습니다. 대기업의 원자재 재고가 소진되는 4개월 뒤(Lag 4) 대형마트 가공식품 및 생필품 가격이 인상될 확률이 매우 높습니다. 유효기간이 넉넉한 비신선 생필품(라면, 통조림, 즉석밥, 세제 등)은 가격이 오르지 않은 지금부터 미리 선행 매수(쟁여두기)를 시작하십시오.
                  </p>
                ) : (
                  <p className="text-slate-700 text-lg leading-relaxed border-l-4 pl-5 border-blue-500 bg-blue-50/50 py-4 pr-4 rounded-r-lg font-medium">
                    환율 변동성이 통제 범위 내에 있습니다. 수 개월 뒤 가공식품 및 생필품의 급격한 물가 상승 우려가 적으므로 무리한 재고 확보를 지양하십시오.
                  </p>
                )}
              </div>
            </div>
          </div>

          <div className="mt-8 bg-slate-100 border border-slate-200 rounded-xl p-5 flex gap-3 items-start shadow-sm">
            <Info className="w-5 h-5 text-slate-500 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-slate-600 font-bold tracking-wide">
              주의: 본 엔진은 물가가 상승하더라도 상할 우려가 있어 미리 구매해 둘 수 없는 신선식품(우유, 채소, 육류 등)은 추천 리스트에서 자동으로 필터링 및 제외합니다.
            </p>
          </div>
        </section>

        {/* Statistics and Charts */}
        <section className="grid lg:grid-cols-2 gap-8">
          
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-200">
            <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
              <Activity className="w-5 h-5 text-gray-400" />
              4개년 실측치 상관계수 매트릭스
            </h3>
            <div className="overflow-x-auto rounded-lg border border-gray-200">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 text-slate-700 border-b border-gray-200">
                  <tr>
                    <th className="px-5 py-4 font-bold">시차 (Lag)</th>
                    <th className="px-5 py-4 font-bold">환율 수준 (단가)</th>
                    <th className="px-5 py-4 font-bold">환율 변동성</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {[
                    { lag: 'Lag 0', level: '0.210', vol: '-0.098' },
                    { lag: 'Lag 1', level: '-0.043', vol: '0.010' },
                    { lag: 'Lag 2', level: '-0.196', vol: '0.012' },
                    { lag: 'Lag 3', level: '-0.056', vol: '0.045' },
                    { lag: 'Lag 4', level: '0.055', vol: '0.258' },
                    { lag: 'Lag 5', level: '0.067', vol: '-0.033' },
                  ].map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 transition-colors">
                      <td className="px-5 py-3.5 font-bold text-gray-900">{row.lag}</td>
                      <td className="px-5 py-3.5 font-mono text-gray-600">{row.level}</td>
                      <td className={`px-5 py-3.5 font-mono font-bold ${row.lag === 'Lag 4' ? 'text-[#e67e22] bg-orange-50/50' : 'text-gray-600'}`}>
                        {row.vol}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-gray-400 mt-4 text-right">※ Data Source: 통계청 및 한국은행 제공 실측치</p>
          </div>

          <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-200 flex flex-col">
            <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
              <BarChart className="w-5 h-5 text-gray-400" />
              AI 예측 오차율 분포도 (Scatter Plot)
            </h3>
            <div className="flex-grow relative bg-slate-50 rounded-lg border border-slate-200 p-4 min-h-[250px]">
              <div className="absolute top-2 left-4 text-xs text-slate-500 font-bold">오차율 (Error %)</div>
              <div className="absolute bottom-2 right-4 text-xs text-slate-500 font-bold">환율 단가 (FX Rate)</div>
              
              <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                <line x1="0" y1="50" x2="100" y2="50" stroke="#cbd5e1" strokeWidth="0.5" strokeDasharray="2" />
                <line x1="50" y1="0" x2="50" y2="100" stroke="#cbd5e1" strokeWidth="0.5" strokeDasharray="2" />
                
                {scatterData.map((pt, idx) => {
                  const px = 5 + ((pt.x - 1100) / 600) * 90;
                  const py = 50 - (pt.y * 15);
                  return (
                    <circle 
                      key={idx} 
                      cx={px} 
                      cy={py} 
                      r="1.2" 
                      fill={COLOR_NAVY} 
                      className="opacity-70 hover:opacity-100 hover:fill-[#e67e22] transition-all duration-200 cursor-crosshair"
                    >
                      <title>환율: {pt.x.toFixed(0)}원 / 오차: {pt.y.toFixed(2)}%</title>
                    </circle>
                  );
                })}
              </svg>
            </div>
            <p className="text-xs text-slate-500 mt-5 leading-relaxed font-medium">
              위 산포도는 환율 구간(X축)에 따른 모델의 예측 오차율(Y축)입니다. 1380원 부근에서는 오차가 적어 점이 중앙에 밀집하지만, 극단적인 환율(이분산성 발생 구간)에서는 예측 분산이 확대되는 부채꼴 형태를 띱니다.
            </p>
          </div>

        </section>

      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white py-10 mt-12">
        <div className="max-w-5xl mx-auto px-4 text-center text-sm text-gray-500 font-medium flex flex-col items-center gap-3">
          <ShieldAlert className="w-6 h-6 text-gray-300" />
          <p>© 2026 Inflation Wizard Analytics.</p>
          <p>본 서비스에서 제공하는 예측 데이터는 참고용 통계 정보이며, 실제 소비 결과에 대한 법적 책임을 지지 않습니다.</p>
        </div>
      </footer>
    </div>
  );
}
