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


struct {
{% for column in columns %}
{% if column.type == "char" %}
    char     {{ column.name }}[{{ column.size }}+1];
{% elif column.type == "double" %}
    double   {{ column.name }};
{% elif column.type == "float" %}
    float    {{ column.name }};
{% elif column.type == "short" %}
    sqlint16 {{ column.name }};
{% elif column.type == "int" %}
    sqlint32 {{ column.name }};
{% elif column.type == "long" %}
    sqlint64 {{ column.name }};
{% endif %}
{% endfor %}
} tmp_{{ tbl_name }};


#endif

