-- -*- mode: sql; coding: utf-8 -*-
-- (c) Valik mailto:vasnake@gmail.com

-- SQL script for Seismodensity project

-- create ALGIS schema
CREATE USER "ALGIS"
    PROFILE "DEFAULT"
    IDENTIFIED BY "12345678"
--	DEFAULT TABLESPACE "TABLE01"
    ACCOUNT UNLOCK;
ALTER USER "ALGIS"
    TEMPORARY TABLESPACE "TEMP"
ALTER USER "ALGIS"
    GRANT "RESOURCE" TO "ALGIS" ;
    GRANT "CONNECT" TO "ALGIS" ;
ALTER USER "ALGIS"
    DEFAULT ROLE "RESOURCE","CONNECT";
commit;


-- create function. Use algis account
drop function algis.calc_seismodensity;
create or replace
function  algis.calc_seismodensity(poly varchar2, poly_wkid number)
    return varchar2 -- плотность, суммарная длина профилей в участке, площадь участка
as
-- Процедура расчета плотности сейсмопрофилей на заданном полигоне;
-- для работы необходимо наличие фичекласса с сейсмопрофилями ALGIS.APP_GP_SEISM2D_L в СК где единицы измерений в метрах
-- также необходимо наличие используемых poly_wkid, суть WKID и соответствующих им SRID в реестре SDE sde.st_spatial_references;
-- проверить работоспособность функции можно запросом
-- select algis.calc_seismodensity('(70 70, 71 72, 85 65, 70 70)', 4326) as calcres from dual;
    res varchar2(100);
    len_km number;
    area_kmsq number;
    dens number;
    profiles_srid number;
    poly_srid number;
    poly_geom "SDE"."ST_GEOMETRY"; -- from WKT polygon, http://en.wikipedia.org/wiki/Well-known_text
begin
    select srid into profiles_srid from sde.st_geometry_columns where table_name like 'APP_GP_SEISM2D_L';
    select srid into poly_srid from sde.st_spatial_references where cs_id = poly_wkid and rownum < 2;
    select sde.st_transform (sde.st_polygon('polygon (' || poly || ')', poly_srid), profiles_srid) into poly_geom from dual;
--~ найти длины отрезков профилей, попадающих внутрь полигона:
    select ( sum (sde.st_length (sde.st_intersection (poly_geom, sp.shape))) / 1000 ) into len_km
        from ALGIS.APP_GP_SEISM2D_L sp	where sde.st_disjoint(poly_geom, sp.shape) = 0;
    if len_km is null then
        len_km := 0;
    end if;
--~ площадь:
    select (sde.st_area (poly_geom) / 1000000 ) into area_kmsq	from dual ;
--~ длины поделить на площадь:
    case
        when area_kmsq is null then area_kmsq := 0.0000001;
        when area_kmsq = 0 then area_kmsq := 0.0000001;
        else null;
    end case;
    dens := len_km / area_kmsq;
    res := '' || to_char(dens, '999.999') || ', ' ||
        to_char(len_km, '999999999.999') || ', ' ||
        to_char(area_kmsq, '999999999.999') || ''; -- km/km^2, km, km^2
    return res;
end;
/
commit;

grant EXECUTE on "ALGIS"."CALC_SEISMODENSITY" to "ALGIS" ;
-- grant EXECUTE on "ALGIS"."CALC_SEISMODENSITY" to "SDE" ;
