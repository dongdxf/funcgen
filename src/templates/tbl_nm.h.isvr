/***********************************************************************
 *  Copyright {{ cr_year }}, China UnionPay Co., Ltd. All rights reserved.
 *
 *  THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF CHINA UNIONPAY CO.,
 *  LTD. THE CONTENTS OF THIS FILE MAY NOT BE DISCLOSED TO THIRD
 *  PARTIES, COPIED OR DUPLICATED IN ANY FORM, IN WHOLE OR IN PART,
 *  WITHOUT THE PRIOR WRITTEN PERMISSION OF CHINA UNIONPAY CO., LTD.
 *
 *
 *
 *  Edit History:
 *      {{ crt_time }} - Created by funcgen.
 *
***********************************************************************/
#ifndef  {{ tabmacro }}
#define  {{ tabmacro }}


typedef struct {
{% for column in columns %}
{% if column.type == "char" %}
    char   {{ column.name }}[{{ column.size }}+1];
{% elif column.type == "double" %}
    double {{ column.name }};
{% elif column.type == "float" %}
    float  {{ column.name }};
{% elif column.type == "short" %}
    short  {{ column.name }};
{% elif column.type == "int" %}
    int    {{ column.name }};
{% elif column.type == "long" %}
    long   {{ column.name }};
{% endif %}
{% endfor %}
} dstr_{{ tbl_name }};


#define  SUCCESS  0
#define  FAILURE  -1

{% for macro in macros %}
{% if macro.comstr == '' %}
#define  {{ macro.name }}  {{ macro.value }}
{% else %}
#define  {{ macro.name }}  {{ macro.value }}    {{ macro.comstr }}
{% endif %}
{% endfor %}


{% if tbl_flag > 1 %}
{% for opr in oprs %}
int {{ tbl_name }}_{{ opr }}(int tbl_flag, int opr_type, dstr_{{ tbl_name }} *p_dstr_{{ tbl_name }}, int *p_sql_code);
{% endfor %}
{% for flag in flags %}

{% for opr in oprs %}
int {{ tbl_name }}0{{ flag }}_{{ opr }}(int opr_type, dstr_{{ tbl_name }} *p_dstr_{{ tbl_name }}, int *p_sql_code);
{% endfor %}
{% endfor %}
{% else %}
{% for opr in oprs %}
int {{ tbl_name }}_{{ opr }}(int opr_type, dstr_{{ tbl_name }} *p_dstr_{{ tbl_name }}, int *p_sql_code);
{% endfor %}
{% endif %}


#endif

