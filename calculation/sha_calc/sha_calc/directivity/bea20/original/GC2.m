%% GC2 MATLAB function
% coded by Jeff Bayless, May 2020.  jeff.bayless@aecom.com
% this is a conversion to MATLAB of Brian Chiou's R functions for the calculation of GC2
% Reference: Spudich, Paul and Chiou, Brian, 2015, Strike-parallel and strike-normal coordinate system around geometrically complicated rupture traces for use by NGA-West2 and further improvements: U.S. Geological Survey Open-File Report 2015-1028, 20 p., https://dx.doi.org/10.3133/ofr20151028.

%% Input parameters:
% ftraces:              a 1xN struct, where N is the number of individual rupture strands, for each strand i:
    % ftraces(i).trace: a nx2 double, where n is the number of cartesian X,Y coordinates defining the surface trace for strand i [km]
    % ftraces(i).l:     a 1x(n-1) double, defining the length of each segment of strand  i [km]
    % ftraces(i).strike:a 1x(n-1) double, defining the strike of each segment of strand  i [degrees]
% SiteX, SiteY:         1xS and 1xs doubles, defining the cartesian coordinates for which to calculate U and T.  If 'gridflag' is set to true, then U and T are calculated for S*s coordinates, otherwise they are calculated point-wise at S coordinates. [km]
% type:                 a struct with two fields:
    % type.str:         a string which determines the method used for calculating the coordinate shift (Eq 12 and 13 in the OFR). Can be 'NGA','JB', or any other string, which defaults to the OFR version.  If set to 'JB' then type.po must be defined.
    % type.po:          a 1x2 double, only used if type.str='JB'. This shifts the coordinate system p_origin for U and T to the location specified, instead of automatically placing it at the endpoint of the nominal strike. 
% discordant:           a 1x1 logical, flag for checking segment discordance (if true)
% gridflag:             a 1x1 logical, flag for calculating the coordinates on a grid (if true), versus at the element-wise coordinates in SiteX and SiteY (if false)

%% Output parameters:
% T,U,W:                the GC2 parameters, either sxS or 1XS doubles depending on 'gridflag' value [km, except for W, which is unitless]
% reference_axis:       the nominal strike direction after correcting for segment discordance, 1x2 unit vector
% p_origin:             the coordinate system origin, 1x2 double [km]
% nominal_strike:       a struct with four fields:
    % nominal_strike.a: trial vector-a, formed by connecting the two endpoints most distance from each other, 2x2 [km]
    % nominal_strike.b: the nominal strike coordinates, 1x2 double [km]
    % nominal_strike.e: the directional dot product for each trace to check for discordance, mx1 double 
    % nominal_strike.E: the sum of nominal_strike.e, 1x1 double
% Upo, Tpo:             the U,T of coordinate type.po (before any shift), which is the shift that has been applied to U and T, both 1x1 doubles [km]
% gradT:                this has not yet been implemented

function [T,U,W,reference_axis,p_origin,nominal_strike,Upo,Tpo]=GC2(ftraces,SiteX,SiteY,type,discordant,gridflag)

    %% call the sub functions 

    % (1) nominal strike
    [nominal_strike] = comp_nominal_strike(ftraces) ;

    % (2) link traces
    [single_trace,reference_axis,p_origin] = linktraces(ftraces, nominal_strike, type, discordant);   
    
    % (3) compute GC2 for stations
    if gridflag % calculate the coordinates on a grid defined by SiteX and SiteY
        T=zeros(length(SiteY),length(SiteX));
        U=zeros(length(SiteY),length(SiteX));
        W=zeros(length(SiteY),length(SiteX));
        for ii=1:length(SiteX)
            for jj=1:length(SiteY)
                    site.StaX=SiteX(ii);
                    site.StaY=SiteY(jj);
                    [T(jj,ii),U(jj,ii),W(jj,ii)] = computeGC2(site,single_trace);
            end
        end
    else % calculate at the S coordinates defined point-wise in SiteX(1:S) and SiteY(1:S)
        T=zeros(1,length(SiteX));
        U=zeros(1,length(SiteX));
        W=zeros(1,length(SiteX));
        for ii=1:length(SiteX)
            site.StaX=SiteX(ii);
            site.StaY=SiteY(ii);
            [T(1,ii),U(1,ii),W(1,ii)] = computeGC2(site,single_trace);
        end
    end
    
    % (4) compute GC2 for the location defined by type.Upo and apply the shift to U
    if strcmp(type.str,'JB')
        site.StaX=type.po(1);
        site.StaY=type.po(2);
        [Tpo,Upo,~] = computeGC2(site,single_trace);
        U=U-Upo;
        T=T-Tpo;
    else
        Upo=0; 
        Tpo=0;
    end
    
    % finished
    
end

%% Step 1, in Brian's code was to convert origin-strike-length to fault trace coordinates; this is the input to the main function above and is therefore skipped
%% Step 2, Compute GC2 Nominal Strike

function [nominal_strike] = comp_nominal_strike(ftraces) 

    % calculate the nominal strike and other parameters for use later in function link_traces
    %  - traces are in arbitrary order; they are not necessarily in the direction of strike  

    % create a matrix of trace ends, two rows per trace        
    m=length(ftraces);
    trace_ends=zeros(m*2,2);
    for jj=1:m
        nseg=length(ftraces(jj).strike);
        trace_ends((jj-1)*2+[1 2],:)=ftraces(jj).trace([1 nseg+1],:);
    end   
    
    % find the two endpoints most distant from each other
    n = size(trace_ends,1);
    maxdist = -1;
    for ii=1:(n-1) 
      for kk = ii+1:n
         dist = norm(trace_ends(kk,:) - trace_ends(ii,:),2);
         if (dist > maxdist) 
           i1 = ii;
           i2 = kk;
           maxdist = dist;
         end
      end
    end
 
% trial vector-a, formed by connecting the two endpoints most distance from each other
    a=trace_ends([i1 i2],:); 
    if a(2, 1) - a(1, 1) < 0
        a = trace_ends([i2, i1],:);
    end
    a_hat = a(2,:) - a(1,:);
    a_hat = a_hat ./ norm(a_hat, 2); % unit vector
    
% projection of end-to-end vector to vector-b_hat
    e = zeros(m,1);
    for jj=1:m
      e(jj,1) = (trace_ends(jj*2,:) - trace_ends(jj*2-1,:)) * a_hat.'; % matrix multiplication
    end
    E = sum(e);
    
% calculate vector-b with strike discordance corrected. 
    b = [0 0];
    for jj=1:m
      if (sign(e(jj)) == sign(E)) 
        b = b + (trace_ends(jj*2,:) - trace_ends(jj*2-1,:)) ;
      else  
        b = b - (trace_ends(jj*2,:) - trace_ends(jj*2-1,:)) ;
      end
    end
    
    nominal_strike.a=a;
    nominal_strike.b=b;
    nominal_strike.e=e;
    nominal_strike.E=E;
    
end

%% Step 3, Link traces; reverse the strike of discordant trace ----

function [single_trace,reference_axis,p_origin] = linktraces(ftraces, nominal_strike, type, discordant)

    m = length(ftraces);
    a = nominal_strike.a;
    b = (nominal_strike.b).';
    e = nominal_strike.e;
    E = nominal_strike.E;
    
    if discordant 
        for jj=1:m 
            if e(jj) * E < 0 % reverse strike, current trace is discordant
                n = size(ftraces(jj).trace,1);
                n1=n-1;
                ftraces(jj).trace  = flipud(ftraces(jj).trace);
                ftraces(jj).l      = fliplr(ftraces(jj).l);
                ftraces(jj).strike = ftraces(jj).strike - 180;
%                 ftraces(jj).p1     = ftraces(jj).trace(1,:); % I (Jeff) have commented this line out
            end
        end
    end

    % reference axis and origin for calculating coordinate shift (this should be in nominal_strike)
    if strcmp(type.str,'NGA2') 
        reference_axis = sign(E) * (a(2,:) - a(1,:));
        if (E < 0) 
          p_origin = a(2,:);
        else
          p_origin = a(1,:);
        end
    else % this is the default case from the OFR, also used for the case 'JB'
        if (a(2,:) - a(1,:)) * b >= 0 
          p_origin = a(1,:) ; 
        else
          p_origin = a(2,:);
        end
        reference_axis =  b.' ;
    end
    reference_axis = reference_axis / norm(reference_axis, 2) ;
    % reference_axis = as.vector(reference_axis) % I (Jeff) have commented this line because it is not needed in MATLAB
    
    % compute U.prime_p1 
    Uprime_p1 = nan(m,1);
    for jj=1:m
        Uprime_p1(jj) = (ftraces(jj).trace(1,:) - p_origin) * reference_axis.'; % matrix mult.
    end
    
    Trace=[]; s=[]; Strike=[]; Len=[];
    for jj=1:m
      ftr = ftraces(jj);
      Trace  = [Trace; ftr.trace];    % link current trace 
      Strike = [Strike ftr.strike nan];  % merge strikes
      Len    = [Len  ftr.l nan];          % merge segment lengths
      s      = [s Uprime_p1(jj) + [0 cumsum(ftraces(jj).l)] ]; % merge s
      s(length(s)) = nan;
    end
  
    % remove the last element which is a nan
    Strike = Strike(1:end-1);
    Len    = Len(1:end-1);
    s      = s(1:end-1);

    single_trace.strike=Strike;
    single_trace.l=Len;
    single_trace.s=s;
    single_trace.ftrace=Trace;
    single_trace.ref_axis=reference_axis;
end
    

%% Step 4, compute GC2

function [T,U,W] = computeGC2(site,single_trace)

    % site is X,Y : Site.StaX, Site.StaY
    % Single-trace version
    
    strike = single_trace.strike;
    l      = single_trace.l;
    s      = single_trace.s;
    nseg   = length(l);
    p_origin = single_trace.ftrace  ;
    p_origin = p_origin(1:nseg,:);  % nseg x 2 matrix (discards the last [nseg+1] coordinate)

    % compute site's (t, u, wgt) w.r.t. each of the nseg coordinate systems
    for iseg=1:nseg
        seg_tuw_List(iseg) = comp_segment_tuw(p_origin(iseg,:), strike(iseg), l(iseg), site) ;
    end

    GC2_U = 0; GC2_T = 0; Wgt   = 0;
    for iseg=1:nseg
      if isnan(l(iseg)) 
          continue  % skip bogus segments
      end
      seg_tuw  = seg_tuw_List(iseg);
      GC2_U = GC2_U + (seg_tuw.u + s(iseg)) * seg_tuw.wgt;
      GC2_T = GC2_T +  seg_tuw.t            * seg_tuw.wgt;
      Wgt   = Wgt   +  seg_tuw.wgt ;
    end
    GC2_U = GC2_U / Wgt;
    GC2_T = GC2_T / Wgt;

    % apply rule #3 to sites located on fault 
    k_onfault =  find(Wgt==inf);
    GC2_T(k_onfault) = 0;
    for kk=k_onfault
      for ii=1:nseg
        if isinf(seg_tuw_List(ii).wgt(kk)) 
          GC2_U(kk) = seg_tuw_List(ii).u(kk) + s(ii);
          Wgt(kk) = nan;
          break % exit the for loop
        end
      end
    end

    T = GC2_T; U = GC2_U; W = Wgt;
end

function [seg_tuw] = comp_segment_tuw(origin, strike, l, Site) 
  
  % compute (t, u, w) with respect to fault coordinate axes defined by (origin, strike, and l)
  strikerad = strike / 180 * pi;
  
  uhat = [sin(strikerad)  cos(strikerad)];
  that = [sin(strikerad + pi/2)  cos(strikerad + pi/2)];
  
  t = (Site.StaX - origin(1)) * that(1) + (Site.StaY - origin(2)) * that(2);
  u = (Site.StaX - origin(1)) * uhat(1) + (Site.StaY - origin(2)) * uhat(2);
  
  % closed form solution to Equation 1 of the OFR
  if isnan(t)
      wgt=nan;
  elseif abs(t) > 1E-6 % rule 1
      wgt=(atan((l - u) / t) - atan(-u / t)) / t;
  elseif u < 0 || u > l % rule 2
      wgt=1 / (u - l) - 1 / u;
  else % rule 3; T=0
      wgt=Inf; 
  end
  
  seg_tuw.t=t;
  seg_tuw.u=u;
  seg_tuw.wgt=wgt;

end 
        
%% Step 5, Gradient of T ----

% this has not been implemented yet