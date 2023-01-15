%%  Matlab function for the Bayless et al. (2020) Directivity Model, as described in USGS External Grants Report G18AP00092
%
%	Jeff Bayless (jeff.bayless@aecom.com) 
%	Created: May 2020
%	Updated: May 2020
%
%	Copyright (c) 2020, Jeff Bayless, covered by BSD License.
%	All rights reserved.
%
%	Redistribution and use in source and binary forms, with or without 
%	modification, are permitted provided that the following conditions are 
%	met:
%
%	   * Redistributions of source code must retain the above copyright 
%	     notice, this list of conditions and the following disclaimer.
%	   * Redistributions in binary form must reproduce the above copyright 
%	     notice, this list of conditions and the following disclaimer in 
%	     the documentation and/or other materials provided with the distribution
%	                           
%	THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
%	AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
%	IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
%	ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE 
%	LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
%	CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
%	SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
%	INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
%	CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
%	ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
%	POSSIBILITY OF SUCH DAMAGE.
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%% INPUT
% M:            Moment magnitude, 5<=M<=8. 1x1 double.
% U,T:          the GC2 coordinates in km. Must both be nX1 doubles where n is the number of locations at which the model provides a prediction. Must be columnar.
% Smax:         the maximum possible values of S for the scenario in km. 1x2 double with the first element corresponding to the maximum S in the antistrike direction (defined to be a negative value) and the second element the maximum in the strike direction (positive value).
% D:            the effective rupture travel width, measured from the hypocenter to the shallowest depth of the rupture plane, up-dip (km). 1x1 double.
% Tbot:         the T ordinate of the bottom of the rupture plane (projected to the surface) in km. 1x1 double.
% Dbot:         the vertical depth of the bottom of the rupture plane from the ground surface, including Ztor, in km. 1x1 double.
% Rake, Dip:    the characteristic rupture rake and dip angles, in degrees. 1x1 doubles. -180<=Rake<=180 and Dip<=90
% ForceType:    a flag for determining the SOF category. 0->select SOF based on rake angle. 1->force SOF=1. 2->force SOF=2. 1x1 double.
% Period:       the spectral period for which fD is requested, in sec. 0.01<Period<10. 1x1 double.

%% OUTPUT 
% fD:           the directivity adjustment in ln units. nx1000 double at 1000 log-spaced periods between 0.01 and 10 sec. The periods are provided in Other.Per
% fDi:          the directivity adjustment in ln units at user provided 'Period'. nx1 double.
% PhiRed:       the phi reduction. nx1000 double.
% PhiRedi:      the phi reduction at user provided 'Period'. nx1 double.
% PredicFuncs:  a struct with five fields:
    % fG:       the period independent geometric directivity predictor. nx1 double.
    % fdist:    the distance taper. nx1 double.
    % ftheta:   the azimuthal predictor function #1. nx1 double.
    % fphi:     the azimuthal predictor function #2. nx1 double.
    % fs2:      the predictor function for the rupture travel distance. nx1 double.
% Other:        a struct with eight fields:
    % Per:      the periods at which fD and PhiRed are provided. 1x1000 double with 1000 log-spaced periods between 0.01 and 10 sec.
    % Rmax:     the maximum distance of the distance taper. 1x1 double.
    % Footprint:the index of sites within the footprint of the directivity effect (those with nonzero distance taper). nx1 logical.
    % Tpeak:    the model peak period of the directivity effect. 1x1 double.
    % fg0:      the model centered value of fG. 1x1 double.
    % bmax:     the maximum slope of the directivity effect. 1x1 double.
    % typeflag: a string which identifies which SOF model has been applied, either 'SOF=1; strike slip' or 'SOF=2; oblique, reverse, normal'
    % S2:       the generalized rupture travel distance parameter. nx1 double.

function [fD,fDi,PhiRed,PhiRedi,PredicFuncs,Other]=Bea20(M,U,T,Smax,D,Tbot,Dbot,Rake,Dip,ForceType,Period)
%% (1) Calculate the period-independent predictors fG, fs2, ftheta, fphi, and distance taper fdist

% (1a) if not specified, determine rupture category from rake angle
    if ForceType==0
        if (Rake>=-30 && Rake<=30) ||  (Rake>=-180 && Rake<=-150) ||  (Rake>=150 && Rake<=180)
            type=1;
            typeflag='SOF=1; strike slip';
        else
            type=2;
            typeflag='SOF=2; oblique, reverse, normal';
        end
    elseif ForceType==1 % specified regardless of rake
        type=1;
        typeflag='SOF=1; strike slip';
    elseif ForceType==2 % specified regardless of rake
        type=2;
        typeflag='SOF=2; oblique, reverse, normal';
    end  

% (1b) Convert U to S
    Smax1=Smax(1);
    Smax2=Smax(2);
    S=zeros(size(U)); 
    uneg=U<0; upos=U>=0; % negative and positive indices of U, S is positive in the direction of strike and negative in the opposite
    S(uneg)=-min(abs(U(uneg)),abs(Smax1)); % converts U to S
    S(upos)=min(abs(U(upos)),abs(Smax2));  % converts U to S

% (1c) convert U to Ry0
    Ry=zeros(size(U));
    Ry(upos)=U(upos)-Smax2;
    Ry(uneg)=abs(U(uneg))-abs(Smax1);
    utween=U<=Smax2 & U>=Smax1; % in between, Ry0=0
    Ry(utween)=0;

% (1d) Calculate S2
    if type==2 && Rake<0 % for primarily normal faulting, flip the sign of S
        S=-S;
    end
    Srake=S.*cosd(Rake); % note this can change the sign of S depending on the rake angle, the resulting negative Srake values are opposite the direction of rake
    sneg=Srake<0; spos=Srake>=0; % indices of pos and neg Srake
    Dmin=3; % minimum value, km
    D=max(D,Dmin);

    S2=sqrt(D.^2+Srake.^2);  % positive everywhere

% (1e) predictor variable fs2
    fs2=zeros(size(U));
        if type==1 % SOF=1: Strike-slip
            fs2=log(S2);
            % apply the cap to Fs, at 465 km or approx. L for a M8, about 6.14 ln units
            fsCap=log(465);
            fs2(fs2>fsCap)=fsCap;

        else % SOF=2: oblique, reverse, normal
            fs2(spos)=log(S2(spos));
            fs2(sneg)=log(D); % for all "negative" S values, set Fs to the value of S2 at U=0
            % apply cap to Fs, at 188 km or the approx. diagonal dimension for a reverse M8, about 5.24 ln units.
            fsCap=log(188);
            fs2(fs2>fsCap)=fsCap;

        end

% (1f) angular predictor variables
    if type==1 % SOF=1: Strike-slip
        % calculate ftheta
        theta=abs(atan(T./U)); theta(isnan(theta))=0; % set to 0 when located exactly on the trace and atan is undefined
        ftheta=abs(cos(2.*theta));

        % calculate fphi
        fphi=ones(size(U)); 

    else % SOF=2: oblique, reverse, normal       
        tpos=T>0; tneg=T<=0;

        % calculate fphi
        phi=zeros(size(U));  % three cases for calculating phi:    
        % (1) T<=0, the footwall
            phi(tneg)=atand((abs(T(tneg))+Tbot)./Dbot)+Dip-90;
        % (2) 0<T<Thyp, the hanging wall short of Tbot
            t1=tpos & T<Tbot;
            phi(t1)=90-Dip-atand((Tbot-T(t1))./Dbot);
        % (3) T>=Tbot, the hanging wall extended past Tbot
            t2=tpos & T>=Tbot;
            phi(t2)=90-Dip+atand((T(t2)-Tbot)./Dbot);
        phi(phi>45)=45; % cap phi at 45 deg, since cos(2*45)=0
        fphi=cosd(2.*phi);                  

        % calculate ftheta
        Tmin=10.*(abs(cosd(Rake))+1);
        T2=max(abs(T),Tmin); % for the FW side
        T2(tpos)=Tmin; % for the HW side

        omega=atan(T2./Ry); % this is the angle made by T2 and Ry, is between [0,pi/2]
        ftheta=sin(omega);  % [0 1]
        ftheta(isnan(ftheta))=1;

    end

% (1g) Distance taper
    % R is the distance from the surface trace
    R=sqrt(T.^2+Ry.^2);    

    % Rmax is linear from 40 km at M5 to 80 km at M7 and higher, for SS. 20 km less for SOF=2
    if M<5 % the minimum magnitude of the model is 5 but this is left here anyway
        Rmax=40;
    elseif M>7
        Rmax=80;
    else
        Rmax=-60+20.*M;
    end
    if type==2
        Rmax=Rmax-20;
    end

    AR=-4*Rmax;
    Footprint=R<=Rmax;  % logical index of sites within the footprint of the directivity effect (nonzero distance taper)
    fdist=zeros(size(R));
    fdist(Footprint)=1-exp(AR./R(Footprint) - AR/Rmax);

% (1h) fG
    fG=fs2.*ftheta.*fphi;
        
%% (2) Calculate fD

% (2a) constants, Table 4-2
    Per=logspace(-2,1,1000);
    coefb=[-0.0336    0.5469]; % mag dependence of bmax  
    coefc=[0.2858   -1.2090]; % mag scaling of Tpeak
    coefd1=[0.9928   -4.8300]; % mag dependence of fG0 for SOF=1
    coefd2=[0.3946   -1.5415]; % mag dependence of fG0 for SOF=2
    SigG=0.4653;


% (2b) impose the limits on M, Table 4-3
    if M>8; M=8; end
    if M<5.5; M=5.5; end

% (2c) determine magnitude dependent parameters
    if type==1
        fG0=coefd1(2)+coefd1(1).*M;   % SOF=1
    else
        fG0=coefd2(2)+coefd2(1).*M;   % SOF=2
    end
    bmax=coefb(2)+coefb(1).*M;   % remove polyval
    Tpeak=10.^(coefc(2)+coefc(1).*M);

% (2d) period dependent coefficients: a and b
    x=log10(Per./Tpeak); % narrow band gaussian centered on Tpeak
    b=bmax.*exp(-x.^2./(2*SigG^2));
    a=-b.*fG0; % the adjustment at fD=0 (y intercept), solves 0=yint + b*x for yint

% (2e) fD and fDi
    fD=(a+fG.*b).*fdist;

    % fD at user requested period
    [~,ti]=min(abs(Per-Period));
    fDi=fD(:,ti);  

        
%% (3) Calculate PhiRed 

% (3a) Coefficient from Table 4-4
    PhiPer=[0.01	0.2	0.25	0.3	0.4	0.5	0.75	1	1.5	2	3	4	5	7.5	10];
    e1= [0.000	0.000	0.008	0.020	0.035	0.051	0.067	0.080	0.084	0.093	0.110	0.139	0.166	0.188	0.199];
    e1interp=interp1(log(PhiPer),e1,log(Per));

% (3b) PhiRed and PhiRedi

    PhiRed=repmat(e1interp,size(fD,1),1);
    PhiRed(not(Footprint),:)=0;

    % PhiRed at user requested period
    PhiRedi=PhiRed(:,ti);
    
%% (4) Format Output    

% period-independent predictor functions
    PredicFuncs.fG=fG;
    PredicFuncs.fdist=fdist;
    PredicFuncs.ftheta=ftheta;
    PredicFuncs.fphi=fphi;
    PredicFuncs.fs2=fs2;

% other 
    Other.Per=Per;
    Other.Rmax=Rmax;
    Other.Footprint=Footprint;
    Other.Tpeak=Tpeak;
    Other.fG0=fG0;
    Other.bmax=bmax;
    Other.typeflag=typeflag;
    Other.S2=S2;

end
