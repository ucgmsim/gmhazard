clear all;close all;clc

%% define the grid of stations X and Y, in km
%SiteX=-80:.5:150;
%SiteY=-80:.5:150;

SiteX=-40:.5:40;
SiteY=-40:.5:40;

##SiteX=175.5:0.05:177.5;
##SiteY=-38:-0.05:-38.7;


%% define the rupture

% the rupture is described as required for use with GC2 (Spudich and Chiou, 2015)
% ftraces is the description of the rupture trace coordinates, strike angles, and segment lengths
% ftraces is a structure with length equal to the number of fault strands, where the strands do not need to be connected at their endpoints.
% for each strand i, ftraces(i).trace lists the X, Y coordinates of the segments which define the strand. this must be (n+1) by 2, where n is the number of segments in the ith strand.
% for each strand i, ftraces(i).strike is a 1xn vector of segment strike angles
% for each strand i, ftraces(i).l is a 1xn vector of segment lengths
% see further descriptions in the accompanying function GC2.m

% to illustrate, these three examples below all define the same rupture in a different way.  Two of them are commented out.

% Option 1: a single strand with a single segment 80 km in length
    %clear ftraces
    %ftraces(1).trace=[0 0;
    %                  0 80];
    %ftraces(1).strike=[0];
    %ftraces(1).l= [80];
    
##    clear ftraces
    ftraces(1).trace=[2.6 2.19;
                      -2.6 -2.19];
    ftraces(1).strike=[230];
    ftraces(1).l= [6.8];

##    clear ftraces
##    ftraces(1).trace=[176.249176 -38.330246;
##                      176.220383 ];
##    ftraces(1).strike=[230];
##    ftraces(1).l= [3.4];

% Option 2: two strands each with one segment 40 km in length
%     clear ftraces
%     ftraces(1).trace=[0 0;
%                       0 40];
%     ftraces(1).strike=[0];
%     ftraces(1).l= [40]; 
% 
%     ftraces(2).trace=[0 40;
%                       0 80];
%     ftraces(2).strike=[0];
%     ftraces(2).l= [40];

% Option 3: one strand with two segments, each 40 km in length
%     clear ftraces
%     ftraces(1).trace=[0 0;
%                       0 40
%                       0 80];
%     ftraces(1).strike=[0 0];
%     ftraces(1).l= [40 40]; 

nt=length(ftraces);

M=5.5; % moment magnitude
ForceType=0; % 0 = base SOF on rake, 1 = force SS SOF, 2 = force non-SS SOF

% select the period at which to show the effect
Tdo=3;

% characteristic rupture parameters
RakeUse=-90;
Dipuse=60;
Wuse=9.2; % down dip width in km
Luse=3.4; % total rupture length in km
ZtorUse=0; % Ztor, must be positive, in km
Rz=ZtorUse./tand(Dipuse); % the distance on the surface from the rupture trace to the point po (only nonzero for Ztor>0 and Dip~=90)
HypDep=6.2349; % hypocenter depth

% specify the coordinates of the epicenter and GC2 origin, po
type.epi=[-2.6 -2.19]; % X, Y
type.po=[-2.6 -2.19]; % in this case, the same as the epicenter

##type.epi=[176.204483 -38.323807]; % X, Y
##type.po=[176.204483 -38.323807]; % in this case, the same as the epicenter
    
%% call the Spudich and Chiou (2015) GC2 function
type.str='JB'; 
discordant=false;
gridflag=true;

[T,U,W,reference_axis,p_origin,nominal_strike,Upo]=GC2(ftraces,SiteX,SiteY,type,discordant,gridflag);

% calculate the maximum value of S in each direction for this hypocenter; it is U calculated at the nominal strike ends
[~,Uend,~,~,~,~,~,~]=GC2(ftraces,nominal_strike.a(1,1),nominal_strike.a(1,2),type,discordant,gridflag);
[~,Uend2,~,~,~,~,~,~]=GC2(ftraces,nominal_strike.a(2,1),nominal_strike.a(2,2),type,discordant,gridflag);
Smax1=min(Uend,Uend2);
Smax2=max(Uend,Uend2); 

%% call the directivity model

D=(HypDep-ZtorUse)./sind(Dipuse); % the updip ordinate from the hypocenter, accounts for buried ruptures
Dbot=ZtorUse+Wuse*sind(Dipuse); 
Tbot=ZtorUse./tand(Dipuse)+Wuse*cosd(Dipuse);
Smax=[Smax1 Smax2];

fDi=zeros(size(U));
for ii=1:size(U,2)
    [fD,fDi(:,ii),PhiRed,PhiRedi,PredicFuncs,Other]=Bea20(M,U(:,ii),T(:,ii),Smax,D,Tbot,Dbot,RakeUse,Dipuse,ForceType,Tdo);
    S2(:,ii)=Other.S2;
    fs2(:,ii)=PredicFuncs.fs2;
    ftheta(:,ii)=PredicFuncs.ftheta;
    fphi(:,ii)=PredicFuncs.fphi;
    fdist(:,ii)=PredicFuncs.fdist;
    fG(:,ii)=PredicFuncs.fG;
    
end  

%% plot U T contours
figure;  set(gcf,'position',[311   188    747 391 ]); 
subplot(1,2,1)
    Z=[fliplr(0:-5:round(min(min(T)))) 5:5:round(max(max(T)))]; % contour interval
    V=[fliplr(0:-20:round(min(min(T)))) 20:20:round(max(max(T)))]; % label interval
    [c,h]=contour(SiteX,SiteY,T,Z); hold on
    clabel(c,h,V)
    for ii=1:nt
        plot(ftraces(ii).trace(:,1),ftraces(ii).trace(:,2),'k','linewidth',2)
    end
    plot(type.epi(1),type.epi(2),'kp','markerfacecolor','r','markersize',12)
    axis square
    title('GC2, T Coordinate')
    xlabel('Easting (km)')
    ylabel('Northing (km)')

subplot(1,2,2)
    Z=[fliplr(0:-5:round(min(min(U)))) 5:5:round(max(max(U)))]; % contour interval
    V=[fliplr(0:-20:round(min(min(U)))) 20:20:round(max(max(U)))]; % label interval
    [c,h]=contour(SiteX,SiteY,U,Z); hold on
    clabel(c,h,V)
    for ii=1:nt
        plot(ftraces(ii).trace(:,1),ftraces(ii).trace(:,2),'k','linewidth',2)
    end
    plot(type.epi(1),type.epi(2),'kp','markerfacecolor','r','markersize',12)
    axis square
    title('GC2, U Coordinate')
    xlabel('Easting (km)')
    ylabel('Northing (km)')

    
 %%  plot the directivity model
 
figure; set(gcf,'position',[402         345        1192         580]);
subplot(2,3,1)
    contourf(SiteX,SiteY,S2); hold on
    colorbar; 
    title('\itS2')
    %colormap(othercolor('BuDRd_18',256))
    for ii=1:nt
        plot(ftraces(ii).trace(:,1),ftraces(ii).trace(:,2),'k','linewidth',2)
    end
    plot(type.epi(1),type.epi(2),'kp','markerfacecolor','r','markersize',12)
    ylabel('Northing (km)')
    axis([min(SiteX) max(SiteX) min(SiteY) max(SiteY)])
subplot(2,3,2)
    contourf(SiteX,SiteY,fs2); hold on
    colorbar; 
    title('\itf_{S2}')
%    colormap(othercolor('BuDRd_18',256))
    for ii=1:nt
        plot(ftraces(ii).trace(:,1),ftraces(ii).trace(:,2),'k','linewidth',2)
    end
    plot(type.epi(1),type.epi(2),'kp','markerfacecolor','r','markersize',12)
    axis([min(SiteX) max(SiteX) min(SiteY) max(SiteY)])
subplot(2,3,3)
    contourf(SiteX,SiteY,ftheta); hold on
    colorbar;
    title('\itf_{\theta}')
    %colormap(othercolor('BuDRd_18',256))
    for ii=1:nt
        plot(ftraces(ii).trace(:,1),ftraces(ii).trace(:,2),'k','linewidth',2)
    end
    plot(type.epi(1),type.epi(2),'kp','markerfacecolor','r','markersize',12)
    axis([min(SiteX) max(SiteX) min(SiteY) max(SiteY)])
subplot(2,3,4)
    contourf(SiteX,SiteY,fG); hold on
    colorbar; 
    title('\itf_G')
    %colormap(othercolor('BuDRd_18',256))
    for ii=1:nt
        plot(ftraces(ii).trace(:,1),ftraces(ii).trace(:,2),'k','linewidth',2)
    end
    plot(type.epi(1),type.epi(2),'kp','markerfacecolor','r','markersize',12)
    xlabel('Easting (km)')
    ylabel('Northing (km)')
    axis([min(SiteX) max(SiteX) min(SiteY) max(SiteY)])
subplot(2,3,5)
    contourf(SiteX,SiteY,fdist); hold on
    colorbar; 
    title('\itf_{dist}')
    %colormap(othercolor('BuDRd_18',256))
    for ii=1:nt
        plot(ftraces(ii).trace(:,1),ftraces(ii).trace(:,2),'k','linewidth',2)
    end
    plot(type.epi(1),type.epi(2),'kp','markerfacecolor','r','markersize',12)
    xlabel('Easting (km)')
    axis([min(SiteX) max(SiteX) min(SiteY) max(SiteY)])
subplot(2,3,6)
    contourf(SiteX,SiteY,exp(fDi)); hold on
    colorbar; 
    title('Amplification, T=3 sec')
    %colormap(othercolor('BuDRd_18',256))
    for ii=1:nt
        plot(ftraces(ii).trace(:,1),ftraces(ii).trace(:,2),'k','linewidth',2)
    end
    plot(type.epi(1),type.epi(2),'kp','markerfacecolor','r','markersize',12)
    xlabel('Easting (km)')
    axis([min(SiteX) max(SiteX) min(SiteY) max(SiteY)])

    
disp('Finished with example script')