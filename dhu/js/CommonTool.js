jQuery.extend({
	// 根据字典编码查询子集，填充到select标签
	getDictItemsByCode: function (options) {
		var contextPath = options.contextPath; //项目路径，固定值'${sessionScope.contextPath}'
		var tagId = options.tagId; 	   			//select标签id
		var dictCode = options.dictCode;			//字典表编码
		var parentId = options.parentId;			//子集所属字典id
		var needParent = options.needParent?options.needParent:false; //是否需要根据所属字典id查询
		var appendEmptyOpt = options.appendEmptyOpt; 		//是否添加空option
		var emptyOptPosition = options.emptyOptPosition; 	//空option添加位置
		var emptyOptVal = options.emptyOptVal?options.emptyOptVal:'';				//空option值
		var emptyOptTxt = options.emptyOptTxt?options.emptyOptTxt:'　';				//空option文本
		var ordered = options.ordered; 				//是否排序
		var sortType = options.sortType; 			//升序/降序
		var orderbycode = options.orderbycode?true:false;
		var orgValue = options.orgValue; 			//默认选中值
		var orgText = options.orgText; 			//默认选中值
		var isMulti = options.isMulti; 				//是否多选
		var separator = options.separator; 			//多选默认选中值分隔符号
		var byClass = options.byClass; 				//是否根据样式查找select
		var tagClass = options.tagClass;			//select样式名称
		var chosenFormat = options.chosenFormat;	//是否格式化chosen
		var notIncludeStr = options.notIncludeStr;	//不包含字符
		var notIncludeStrArray = options.notIncludeStrArray||[];	//不包含字符（多个）
		var appointSelected = options.appointSelected; //指定第几个选项选中（非头尾补充选项）（优先级低于orgValue）
		var pointPlus = 0;//跳过不包含个数
		var asyncType = (options.asyncType?options.asyncType:false);
		var autoWidth = (options.autoWidth?options.autoWidth:false);//下拉框自适应宽度（一个字符15px）
		var maxWidthLen = 0;
		var isName=options.isName?true:false
		var defaultRXN = ('undefined'==typeof(options.defaultRXN)?true:options.defaultRXN);//DB_HB_RXN特殊处理：默认去掉s结尾的选项
		if ('DB_HB_RXN' == dictCode) {
			if (defaultRXN) {
				notIncludeStr = 's';
			}
		}
		var selector = '#' + tagId;
		if (null!=byClass && byClass) {
			selector = 'select.'+(null==tagClass?'NNNNNNULL':tagClass);
		}

		$.ajax({
			url: contextPath + '/common/dictSS',
			type: 'POST',
			dataType: 'json',
			async: asyncType,
			data: {
				'dictCode': dictCode,
				'parentId': parentId,
				'needParent': needParent,
				'ordered': ordered,
				'sortType': sortType,
				'orderbycode': orderbycode
			},
			success: function (result) {
				var optionHtml = '';
				$(selector).empty();
				if (appendEmptyOpt && 'top' == emptyOptPosition) {
					optionHtml += '<option value="'+emptyOptVal+'">'+emptyOptTxt+'</option>';
				}
				if (result.success && result.dictSS && 0 < result.dictSS.length) {
					if ($.stringIsEmpty(orgValue) && $.stringIsEmpty(orgText)) {
						
						for (var i = 0; i < result.dictSS.length; i++) {
							var curOptLen = $.getChineseCharLen(result.dictSS[i].name);
	 						if (maxWidthLen < curOptLen) {
	 							maxWidthLen = curOptLen;
	 						}
							var appointSel = '';
							if (appointSelected && i==(appointSelected+pointPlus-1)) {
								appointSel = ' selected="selected" ';
							}
							 if(isName){
								if ((null==notIncludeStrArray || 0==notIncludeStrArray.length) &&
									(null==notIncludeStr || ''==notIncludeStr)) {
								optionHtml += '<option value="' + result.dictSS[i].name + '"'+appointSel+'>' + result.dictSS[i].name + '</option>';
								} else {
										if (0 < notIncludeStrArray.length) {
											var removeNotInclude = false;
											for (var it=0; it<notIncludeStrArray.length; it++) {
												if (-1 < result.dictSS[i].name.indexOf(notIncludeStrArray[it])) {
													removeNotInclude = true;
												}
											}
											if (!removeNotInclude) {
												optionHtml += '<option value="' + result.dictSS[i].name + '"'+appointSel+'>' + result.dictSS[i].name + '</option>';
											} else {
												pointPlus++;
											}
										} 
										else {
											if (0 > result.dictSS[i].name.indexOf(notIncludeStr)) {
												optionHtml += '<option value="' + result.dictSS[i].name + '"'+appointSel+'>' + result.dictSS[i].name + '</option>';
											} else {
												pointPlus++;
											}
										}
									}
							}else if ((null==notIncludeStrArray || 0==notIncludeStrArray.length) &&
									(null==notIncludeStr || ''==notIncludeStr)) {
								optionHtml += '<option value="' + result.dictSS[i].id + '"'+appointSel+'>' + result.dictSS[i].name + '</option>';
							} else {
								if (0 < notIncludeStrArray.length) {
									var removeNotInclude = false;
									for (var it=0; it<notIncludeStrArray.length; it++) {
										if (-1 < result.dictSS[i].name.indexOf(notIncludeStrArray[it])) {
											removeNotInclude = true;
										}
									}
									if (!removeNotInclude) {
										optionHtml += '<option value="' + result.dictSS[i].id + '"'+appointSel+'>' + result.dictSS[i].name + '</option>';
									} else {
										pointPlus++;
									}
								} 
								else {
									if (0 > result.dictSS[i].name.indexOf(notIncludeStr)) {
										optionHtml += '<option value="' + result.dictSS[i].id + '"'+appointSel+'>' + result.dictSS[i].name + '</option>';
									} else {
										pointPlus++;
									}
								}
							}
						}
					} else {
						orgValue = orgValue+'';
						orgText = orgText+'';
						if (null!=isMulti && isMulti) {
							var orgVals = orgValue.split(null==separator?',':separator);
							var orgTxts = orgText.split(null==separator?',':separator);
							for (var i = 0; i < result.dictSS.length; i++) {
								var curOptLen = $.getChineseCharLen(result.dictSS[i].name);
		 						if (maxWidthLen < curOptLen) {
		 							maxWidthLen = curOptLen;
		 						}
								optionHtml += '<option value="' + result.dictSS[i].id + '" '+((orgVals.containsPrecise(result.dictSS[i].id)||orgTxts.containsPrecise(result.dictSS[i].name))?'selected':'')+'>' + result.dictSS[i].name + '</option>';
							}
						} else {
							
							for (var i = 0; i < result.dictSS.length; i++) {
								var curOptLen = $.getChineseCharLen(result.dictSS[i].name);
		 						if (maxWidthLen < curOptLen) {
		 							maxWidthLen = curOptLen;
		 						}
								  if(isName){
									if ((null==notIncludeStrArray || 0==notIncludeStrArray.length) &&
											(null==notIncludeStr || ''==notIncludeStr)) {
										optionHtml += '<option value="' + result.dictSS[i].name + '" '+(orgValue==result.dictSS[i].id||orgText==result.dictSS[i].name?'selected':'')+'>' + result.dictSS[i].name + '</option>';
									}else {
										
										if (0 < notIncludeStrArray.length) {
											var removeNotInclude = false;
											for (var it=0; it<notIncludeStrArray.length; it++) {
												if (-1 < result.dictSS[i].name.indexOf(notIncludeStrArray[it])) {
													removeNotInclude = true;
												}
											}
											if (!removeNotInclude) {
												optionHtml += '<option value="' + result.dictSS[i].id + '" '+(orgValue==result.dictSS[i].id||orgText==result.dictSS[i].name?'selected':'')+'>' + result.dictSS[i].name + '</option>';
											} else {
												pointPlus++;
											}
										} else {
											if (0 > result.dictSS[i].name.indexOf(notIncludeStr)) {
												optionHtml += '<option value="' + result.dictSS[i].id + '" '+(orgValue==result.dictSS[i].id||orgText==result.dictSS[i].name?'selected':'')+'>' + result.dictSS[i].name + '</option>';
											}
										}
									}
								}else if ((null==notIncludeStrArray || 0==notIncludeStrArray.length) &&
										(null==notIncludeStr || ''==notIncludeStr)) {
									optionHtml += '<option value="' + result.dictSS[i].id + '" '+(orgValue==result.dictSS[i].id||orgText==result.dictSS[i].name?'selected':'')+'>' + result.dictSS[i].name + '</option>';
								}else {
									
									if (0 < notIncludeStrArray.length) {
										var removeNotInclude = false;
										for (var it=0; it<notIncludeStrArray.length; it++) {
											if (-1 < result.dictSS[i].name.indexOf(notIncludeStrArray[it])) {
												removeNotInclude = true;
											}
										}
										if (!removeNotInclude) {
											optionHtml += '<option value="' + result.dictSS[i].id + '" '+(orgValue==result.dictSS[i].id||orgText==result.dictSS[i].name?'selected':'')+'>' + result.dictSS[i].name + '</option>';
										} else {
											pointPlus++;
										}
									} else {
										if (0 > result.dictSS[i].name.indexOf(notIncludeStr)) {
											optionHtml += '<option value="' + result.dictSS[i].id + '" '+(orgValue==result.dictSS[i].id||orgText==result.dictSS[i].name?'selected':'')+'>' + result.dictSS[i].name + '</option>';
										}
									}
								}
							}
						}
					}
					if (appendEmptyOpt && 'tail' == emptyOptPosition) {
						optionHtml += '<option value="'+emptyOptVal+'">'+emptyOptTxt+'</option>';
					}
				} else {
					optionHtml += '<option value="'+emptyOptVal+'">'+emptyOptTxt+'</option>';
				}
				// 填充option
				var selector = '#' + tagId;
				if (null!=byClass && byClass) {
					selector = 'select.'+(null==tagClass?'NNNNNNULL':tagClass);
					$(selector).empty();
					$(selector).each(function(){
						$(this).append(optionHtml);
					});
				} else {
					$(selector).empty();
					$(selector).append(optionHtml);
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
					if (null!=byClass && byClass) {
						$(selector).each(function(){
							$(this).attr('data-placeholder', ' ');
							$(this).chosen({no_results_text:'没有结果匹配'});
						});
					} else {
						$(selector).chosen('destroy');
						$(selector+'_chzn').remove();
						$(selector).removeClass('chzn-done');
						$(selector).attr('data-placeholder', ' ');
						$(selector).chosen({no_results_text:'没有结果匹配'});
					}

					if (autoWidth) {
 	 					if ($.chosenDropDefaultWidth() < (maxWidthLen*15/2+50)) {
 	 						$('#'+tagId+'_chzn .chzn-drop').css('width', (maxWidthLen*15/2+50)+'px');
 	 					}
 	 				}
				} else {
					if (isMulti) {
						$(selector).multiselect({
				            nonSelectedText: "请选择",
				            allSelectedText: "全选",
				            nSelectedText: '选中',
				            filterPlaceholder: '搜索',
				            numberDisplayed: 6,//选中大于6个表现显示选中数量
				            buttonWidth: '220px',
				            maxHeight: 300,
				            enableFiltering: true,
				            templates: {
				                button: "<button type='button' class='multiselect dropdown-toggle'   data-toggle='dropdown' style='margin-bottom: 0px'><span class='multiselect-selected-text'></span> <b class='caret'></b></button>",
				                filterClearBtn: ""
				            }, onChange: function (element) {
				                $(element).parent().blur();
				            }
				        });
						$("input:checkbox").uniform();
					}
				}
			},
			error: function (msg) {}
		});
	}

	// 查询所有专业，填充到select标签
	,getAllMajors: function(options) {
		var contextPath = options.contextPath;	//项目根路径
		var tagId = options.tagId;	//select标签id
		var orgMajorId = options.orgMajorId;	//回显值
		var appendEmptyOpt = options.appendEmptyOpt;	//是否添加空选项
		var emptyOptPosition = options.emptyOptPosition;	//空选项位置
		var emptyOptVal = options.emptyOptVal?options.emptyOptVal:'';				//空option值
		var emptyOptTxt = options.emptyOptTxt?options.emptyOptTxt:'　';				//空option文本
		var exclude = options.exclude;	//是否剔除选项
		var excludeSS = options.excludeSS;	//剔除选项
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var showNotInUse = null==options.showNotInUse?true:false;//是否显示未启用任务
		var asyncType = (options.asyncType?options.asyncType:false);
		var autoWidth = (options.autoWidth?options.autoWidth:false);//下拉框自适应宽度（一个字符15px）
		var maxWidthLen = 0;
		$.ajax({
			url:contextPath+'/common/majorSS',
 			type:'POST',
 			dataType:'json',
 			data: {'ordered':true, 'sortType':'asc'},
 			async: asyncType,
 			success:function(result){
 				$('#'+tagId).empty();
 				if (appendEmptyOpt && 'top' == emptyOptPosition) {
 					$('#'+tagId).append('<option value="'+emptyOptVal+'">'+emptyOptTxt+'</option>');
 				}
 				if (result.success && result.majorSS && 0<result.majorSS.length)
 				{
 					for (var i=0; i<result.majorSS.length; i++) {
 						var curOptLen = $.getChineseCharLen(result.majorSS[i].name);
 						if (maxWidthLen < curOptLen) {
 							maxWidthLen = curOptLen;
 						}
 						if (!showNotInUse && 1!=result.majorSS[i].status) {
 							// do nothing
 						} else {
 							if (null==orgMajorId || ''==orgMajorId) {
 	 							$('#'+tagId).append('<option value="'+result.majorSS[i].id+'">'+result.majorSS[i].name+'</option>');
 	 						} else {
 	 							$('#'+tagId).append('<option value="'+result.majorSS[i].id+'" '+(orgMajorId==result.majorSS[i].id?'selected':'')+'>'+result.majorSS[i].name+'</option>');
 	 						}
 						}
 					}
 					if (appendEmptyOpt && 'tail' == emptyOptPosition) {
						$('#' + tagId).append('<option value="'+emptyOptVal+'">'+emptyOptTxt+'</option>');
					}
 				}

 				if (chosenFormat && 0<$('#'+tagId+' option').length) {
 					$('#'+tagId).chosen('destroy');
 	 				$('#'+tagId+'_chzn').remove();
 	 				$('#'+tagId).removeClass('chzn-done');
 	 				$('#'+tagId).attr('data-placeholder', ' ');
 	 				$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
 	 				if (autoWidth) {
 	 					if ($.chosenDropDefaultWidth() < (maxWidthLen*15/2+50)) {
 	 						$('#'+tagId+'_chzn .chzn-drop').css('width', (maxWidthLen*15/2+50)+'px');
 	 					}
 	 				}
 				}
 			},
			error:function(msg){

			}
		});
	}

	// 查询所有专业，填充到select标签
	,getAllMajorsByCollegeId: function(options) {
		var contextPath = options.contextPath;	//项目根路径
		var tagId = options.tagId;	//select标签id
		var orgMajorId = options.orgMajorId;	//回显值
		var appendEmptyOpt = options.appendEmptyOpt;	//是否添加空选项
		var emptyOptPosition = options.emptyOptPosition;	//空选项位置
		var emptyOptVal = options.emptyOptVal?options.emptyOptVal:'';				//空option值
		var emptyOptTxt = options.emptyOptTxt?options.emptyOptTxt:'　';				//空option文本
		var exclude = options.exclude;	//是否剔除选项
		var excludeSS = options.excludeSS;	//剔除选项
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var collegeId = options.collegeId;//学院ID
		var showNotInUse = null==options.showNotInUse?true:false;//是否显示未启用任务
		var asyncType = (options.asyncType?options.asyncType:false);
		var autoWidth = (options.autoWidth?options.autoWidth:false);//下拉框自适应宽度（一个字符15px）
		var appointMinWidth = (options.appointMinWidth?options.appointMinWidth:null);
		var crossAcad = (null!=options.crossAcad?options.crossAcad:false);
		var isMulti = (null==options.isMulti?false:options.isMulti);
		var isMultiShowAll = (null==options.isMultiShowAll?false:options.isMultiShowAll);
		var multiWidth = (null==options.multiWidth?220:options.multiWidth);
		var maxWidthLen = 0;
		$.ajax({
			url:contextPath+'/common/majorSSByCollegeId',
			type:'POST',
			dataType:'json',
			data: {'ordered':true, 'sortType':'asc', 'collegeId':collegeId, crossAcad:crossAcad},
			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();
				if (appendEmptyOpt && 'top' == emptyOptPosition) {
					$('#'+tagId).append('<option value="'+emptyOptVal+'">'+emptyOptTxt+'</option>');
				}
				if (result.success && result.majorSS && 0<result.majorSS.length)
				{
					for (var i=0; i<result.majorSS.length; i++) {
						var curOptLen = $.getChineseCharLen(result.majorSS[i].name);
 						if (maxWidthLen < curOptLen) {
 							maxWidthLen = curOptLen;
 						}
						if (!showNotInUse && 1!=result.majorSS[i].status) {
							// do nothing
						}else {
							if (null==orgMajorId || ''==orgMajorId) {
								$('#'+tagId).append('<option value="'+result.majorSS[i].id+'">'+result.majorSS[i].name+'</option>');
							} else {
								$('#'+tagId).append('<option value="'+result.majorSS[i].id+'" '+(orgMajorId==result.majorSS[i].id?'selected':'')+'>'+result.majorSS[i].name+'</option>');
							}
						}
					}
					if (appendEmptyOpt && 'tail' == emptyOptPosition) {
						$('#' + tagId).append('<option value="'+emptyOptVal+'">'+emptyOptTxt+'</option>');
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
					$('#'+tagId).chosen('destroy');
					$('#'+tagId+'_chzn').remove();
					$('#'+tagId).removeClass('chzn-done');
					$('#'+tagId).attr('data-placeholder', ' ');
					$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
					if (autoWidth) {
						var minWidth = (null!=appointMinWidth?appointMinWidth:$.chosenDropDefaultWidth());
 	 					if (minWidth < (maxWidthLen*15/2+50)) {
 	 					// if ($.chosenDropDefaultWidth() < (maxWidthLen*15/2+50)) {
 	 						$('#'+tagId+'_chzn .chzn-drop').css('width', (maxWidthLen*15/2+50)+'px');
 	 					}
 	 				}
				} else {
					if (isMulti) {
						$('#'+tagId).multiselect({
							nonSelectedText: "请选择",
							allSelectedText: "全选",
							nSelectedText: '选中',
							filterPlaceholder: '搜索',
							numberDisplayed: 10,//选中大于6个表现显示选中数量
							buttonWidth: multiWidth+'px',
							maxHeight: 300,
							enableFiltering: true,
							templates: {
								button: isMultiShowAll?("<button type='button' class='multiselect dropdown-toggle'   data-toggle='dropdown' style='margin-bottom: 0px'><span class='multiselect-selected-text' style='display:block;word-break:break-all;white-space:normal;width:"+(multiWidth-28)+"px;'></span> <b class='caret'></b></button>"):("<button type='button' class='multiselect dropdown-toggle'   data-toggle='dropdown' style='margin-bottom: 0px'><span class='multiselect-selected-text'></span> <b class='caret'></b></button>"),
								filterClearBtn: ""
							}, onChange: function (element) {
								$(element).parent().blur();
							}
						});
						$("input:checkbox").uniform();
					}
				}
			},
			error:function(msg){

			}
		});
	}

	// 查询所有组织机构，填充到select标签
	,getAllOrgnizations: function(options) {
		var contextPath = options.contextPath; //项目根路径
		var tagId = options.tagId; //select标签id
		var orgOrgnId = options.orgOrgnId;//回显值
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var orgnType = options.orgnType;//是否格式化chosen
		var asyncType = (options.asyncType?options.asyncType:false);
		var isAcademy=(options.isAcademy==true?1:0);
		var autoWidth = (null!=options.autoWidth?options.autoWidth:false);//下拉框自适应宽度（一个字符15px）
		var ordered = (null!=options.ordered?options.ordered:true);
		var isMulti = options.isMulti; 				//是否多选
		var fixedOrgn = options.fixedOrgn||null;
		var appointScope = options.appointScope||null;
		var bHasAllSchool=options.bHasAllSchool||false;//如果为true，剔除全校选项
		var appendEmptyOpt = (null!=options.appendEmptyOpt?options.appendEmptyOpt:true);	//是否添加空选项
		var maxWidthLen = 0;
		$.ajax({
			url:contextPath+'/common/orgnSS',
 			type:'POST',
 			dataType:'json',
 			data: {'ordered':ordered, 'sortType':'asc', 'orgnType':orgnType,'isAcademy':isAcademy},
 			async: asyncType,
 			success:function(result){
 				$('#'+tagId).empty();
 				if (appendEmptyOpt) {
 					$('#'+tagId).append('<option value="">　</option>');
				}
 				if (result.success && result.orgnSS && 0<result.orgnSS.length)
 				{
					if(bHasAllSchool){//如果为true，剔除全校选项
						var nAllSchoolIdx=-1
						for(var j=0;j<result.orgnSS.length;j++){
							if(result.orgnSS[j].id===61){
								nAllSchoolIdx=j
								break
							}
						}
						if(nAllSchoolIdx>-1){
							result.orgnSS.splice(nAllSchoolIdx,1)
						}
					}

 					if (appointScope) {
 						appointScope = ','+appointScope+',';
						for (var i=0; i<result.orgnSS.length; i++) {
							if (-1 == appointScope.indexOf(','+result.orgnSS[i].id+',')) {
								continue;
							}
							if (null!=fixedOrgn && fixedOrgn!=result.orgnSS[i].id) {
								continue;
							}
							var curOptLen = $.getChineseCharLen(result.orgnSS[i].name);
							if (maxWidthLen < curOptLen) {
								maxWidthLen = curOptLen;
							}
							if (null==orgOrgnId || ''==orgOrgnId) {
								$('#'+tagId).append('<option value="'+result.orgnSS[i].id+'">'+result.orgnSS[i].name+'</option>');
							} else {
								$('#'+tagId).append('<option value="'+result.orgnSS[i].id+'" '+(orgOrgnId==result.orgnSS[i].id?'selected':'')+'>'+result.orgnSS[i].name+'</option>');
							}
						}
					} else {
						for (var i=0; i<result.orgnSS.length; i++) {
							if (null!=fixedOrgn && fixedOrgn!=result.orgnSS[i].id) {
								continue;
							}
							var curOptLen = $.getChineseCharLen(result.orgnSS[i].name);
							if (maxWidthLen < curOptLen) {
								maxWidthLen = curOptLen;
							}
							if (null==orgOrgnId || ''==orgOrgnId) {
								$('#'+tagId).append('<option value="'+result.orgnSS[i].id+'">'+result.orgnSS[i].name+'</option>');
							} else {
								$('#'+tagId).append('<option value="'+result.orgnSS[i].id+'" '+(orgOrgnId==result.orgnSS[i].id?'selected':'')+'>'+result.orgnSS[i].name+'</option>');
							}
						}
					}
 				}

 				if (chosenFormat && 0<$('#'+tagId+' option').length) {
 					$('#'+tagId).chosen('destroy');
 	 				$('#'+tagId+'_chzn').remove();
 	 				$('#'+tagId).removeClass('chzn-done');
 	 				$('#'+tagId).attr('data-placeholder', ' ');
 	 				$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
 	 				if (autoWidth) {
 	 					if ($.chosenDropDefaultWidth() < (maxWidthLen*15/2+50)) {
 	 						$('#'+tagId+'_chzn .chzn-drop').css('width', (maxWidthLen*15/2+50)+'px');
 	 					}
 	 				}
 				}
 			},
			error:function(msg){

			}
		});
	}

	// 查询所有组织机构，填充到select标签
	,getAllOrgnizationsContainorgCode: function(options) {
		var contextPath = options.contextPath; //项目根路径
		var tagId = options.tagId; //select标签id
		var orgOrgnId = options.orgOrgnId;//回显值
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var orgnType = options.orgnType;//学院类型
		var sortType = options.sortType;//排序方式
		var ordered = options.ordered;//是否排序
		var asyncType = (options.asyncType?options.asyncType:false);
		var autoWidth = (options.autoWidth?options.autoWidth:false);//下拉框自适应宽度（一个字符15px）
		var maxWidthLen = 0;
		var orgCode = options.orgCode||false;
		var isAll=options.isAll||false;
		$.ajax({
			url:contextPath+'/sec/getOrgForSelect',
			type:'POST',
			dataType:'json',
			data: {'ordered':ordered, 'sortType':sortType, 'orgnType':orgnType},
			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();
				//$('#'+tagId).append('<option value="">　</option>');
				if (result.success && result.list && 0<result.list.length)
				{
					if(isAll){
						$('#'+tagId).append('<option value="">全部</option>');
					}
					for (var i=0; i<result.list.length; i++) {
						var view = result.list[i].orgName + "(" + result.list[i].orgCode + ")";
						var curOptLen = $.getChineseCharLen(view);
						if (maxWidthLen < curOptLen) {
							maxWidthLen = curOptLen;
						}
						if (null==orgOrgnId || ''==orgOrgnId) {
							$('#'+tagId).append('<option value="'+result.list[i].id+'">'+view+'</option>');
						}else if(orgCode){
							$('#'+tagId).append('<option value="'+result.list[i].orgCode+'" '+(orgOrgnId==result.list[i].orgCode?'selected':'')+'>'+view+'</option>');
						}
						 else {
							$('#'+tagId).append('<option value="'+result.list[i].id+'" '+(orgOrgnId==result.list[i].orgCode?'selected':'')+'>'+view+'</option>');
						}
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
					$('#'+tagId).chosen('destroy');
					$('#'+tagId+'_chzn').remove();
					$('#'+tagId).removeClass('chzn-done');
					$('#'+tagId).attr('data-placeholder', ' ');
					$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
					if (autoWidth) {
						if ($.chosenDropDefaultWidth() < (maxWidthLen*15/2+50)) {
							$('#'+tagId+'_chzn .chzn-drop').css('width', (maxWidthLen*15/2+50)+'px');
						}
					}
				}
			},
			error:function(msg){

			}
		});
	}

	// 查询所有学期，填充到select标签
	,getAllSemesters: function(options) {
		var contextPath = options.contextPath; //项目根路径
		var tagId = options.tagId; //select标签id
		var orgSemeId = options.orgSemeId;//回显值
		var isCurrent=options.isCurrent;//是否显示当前学期
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var asyncType = (options.asyncType?options.asyncType:false);
		var emptyText = (null!=options.emptyText?options.emptyText:'　');
		var codeValue = (options.codeValue?options.codeValue:false)
		var isEmptyOption=options.isEmptyOption//是否有空值，默认有空值
		$.ajax({
			url:contextPath+'/common/semesterSS',
			type:'POST',
			dataType:'json',
			data: {'ordered':true, 'sortType':'desc'},
 			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();
				if(!isEmptyOption){
					$('#'+tagId).append('<option value="">'+emptyText+'</option>');
				}
				if (result.success && result.semesterSS && 0<result.semesterSS.length)
				{
					for (var i=0; i<result.semesterSS.length; i++) {
						if (null==orgSemeId || ''==orgSemeId) {
							if(isCurrent) {
								$('#' + tagId).append('<option value="' + (codeValue?result.semesterSS[i].name:result.semesterSS[i].id) + '"' + (result.semesterSS[i].current == 1 ? 'selected' : '') + '>' + result.semesterSS[i].name + '</option>');
							}else{
								$('#' + tagId).append('<option value="' + (codeValue?result.semesterSS[i].name:result.semesterSS[i].id) + '">' + result.semesterSS[i].name + '</option>');
							}
						} else {
							$('#'+tagId).append('<option value="'+(codeValue?result.semesterSS[i].name:result.semesterSS[i].id)+'" '+(orgSemeId==result.semesterSS[i].id?'selected':'')+'>'+result.semesterSS[i].name+'</option>');
						}
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
 					$('#'+tagId).chosen('destroy');
 	 				$('#'+tagId+'_chzn').remove();
 	 				$('#'+tagId).removeClass('chzn-done');
 	 				$('#'+tagId).attr('data-placeholder', ' ');
 	 				$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
 				}
			},
			error:function(msg){

			}
		});
	}

	// 查询所有学期，填充到select标签
	,getAllSemesters2: function(options) {
		var contextPath = options.contextPath; //项目根路径
		var tagId = options.tagId; //select标签id
		var orgSemeId = options.orgSemeId;//回显值
		var isCurrent=options.isCurrent;//是否显示当前学期
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var asyncType = (options.asyncType?options.asyncType:false);
		var emptyText = (null!=options.emptyText?options.emptyText:'　');
		$.ajax({
			url:contextPath+'/common/semesterSS',
			type:'POST',
			dataType:'json',
			data: {'ordered':true, 'sortType':'desc'},
			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();
				$('#'+tagId).append('<option value="">'+emptyText+'</option>');
				if (result.success && result.semesterSS && 0<result.semesterSS.length)
				{
					for (var i=0; i<result.semesterSS.length; i++) {
						if (null==orgSemeId || ''==orgSemeId) {
							if(isCurrent) {
								$('#' + tagId).append('<option value="' + result.semesterSS[i].name + '"' + (result.semesterSS[i].current == 1 ? 'selected' : '') + '>' + result.semesterSS[i].name + '</option>');
							}else{
								$('#' + tagId).append('<option value="' + result.semesterSS[i].name + '">' + result.semesterSS[i].name + '</option>');
							}
						} else {
							$('#'+tagId).append('<option value="'+result.semesterSS[i].name+'" '+(orgSemeId==result.semesterSS[i].id?'selected':'')+'>'+result.semesterSS[i].name+'</option>');
						}
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
					$('#'+tagId).chosen('destroy');
					$('#'+tagId+'_chzn').remove();
					$('#'+tagId).removeClass('chzn-done');
					$('#'+tagId).attr('data-placeholder', ' ');
					$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
				}
			},
			error:function(msg){

			}
		});
	},getAllYear: function(options) {
		var contextPath = options.contextPath; //项目根路径
		var tagId = options.tagId; //select标签id
		var orgSemeId = options.orgSemeId;//回显值
		var isCurrent=options.isCurrent;//是否显示当前学期
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var asyncType = (options.asyncType?options.asyncType:false);
		var emptyText = (null!=options.emptyText?options.emptyText:'　');
		var codeValue = (options.codeValue?options.codeValue:false);
		$.ajax({
			type:'get',
			url:contextPath+'/DissertationBusiness/getXnList',
			dataType: 'json',
			async:false,
			success:function(result){
				$('#'+tagId).empty();
				$('#'+tagId).append('<option value="">'+emptyText+'</option>');
				if (result.success && result.orgnSS && 0<result.orgnSS.length)
				{
					for (var i=0; i<result.orgnSS.length; i++) {
						if (null==orgSemeId || ''==orgSemeId) {
							if(isCurrent) {
								$('#' + tagId).append('<option value="' + (codeValue?result.orgnSS[i].name:result.orgnSS[i].id) + '"' + (result.orgnSS[i].iscurrent == '是' ? 'selected' : '') + '>' + result.orgnSS[i].name + '</option>');
							}else{
								$('#' + tagId).append('<option value="' + (codeValue?result.orgnSS[i].name:result.orgnSS[i].id) + '">' + result.orgnSS[i].name + '</option>');
							}
						} else {
							$('#'+tagId).append('<option value="'+(codeValue?result.orgnSS[i].name:result.orgnSS[i].id)+'" '+(orgSemeId==result.semeorgnSSsterSS[i].id?'selected':'')+'>'+result.orgnSS[i].name+'</option>');
						}
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
 					$('#'+tagId).chosen('destroy');
 	 				$('#'+tagId+'_chzn').remove();
 	 				$('#'+tagId).removeClass('chzn-done');
 	 				$('#'+tagId).attr('data-placeholder', ' ');
 	 				$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
 				}
			},
			error:function(msg){

			}
		});
	}// 查询所有学期，填充到select标签
	,getSemesterData: function(options) {
		var contextPath = options.contextPath; //项目根路径
		var tagId = options.tagId; //select标签id
		var majorId = options.majorId;//专业id
		var studentNo = options.studentNo;//学号
		var orgClassId = options.orgClassId;//回显值
		var isDisabled=options.disabled
		var ordered = (null==options.ordered?true:options.ordered);//是否排序，默认排序
		var sortType = (this.stringIsEmpty(options.sortType)?'desc':options.sortType);//排序类型，默认降序
		var sortColumn = options.sortColumn;//排序字段
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var asyncType = (options.asyncType?options.asyncType:false);
		$.ajax({
			type:'POST',
			url:contextPath+'/common/orgnSS',
			dataType: 'json',
			data: {'ordered':true, 'sortType':'asc', 'orgnType':'','isAcademy':0},
			async:false,
			success:function(result){
				$('#'+tagId).empty();
				$('#'+tagId).append('<option value="">　</option>');
				if (result.success && result.orgnSS && 0<result.orgnSS.length)
				{
					for (var i=0; i<result.orgnSS.length; i++) {
						if (null==orgClassId || ''==orgClassId) {
							if(i==0){
								$('#'+tagId).append('<option value="'+result.orgnSS[i].id+'" selected>'+result.orgnSS[i].name+'</option>');
							}else{
								$('#'+tagId).append('<option value="'+result.orgnSS[i].id+'">'+result.orgnSS[i].name+'</option>');
							}
						} else {
							if(isDisabled==1){
								if(orgClassId==result.orgnSS[i].id){
									$('#'+tagId).append('<option value="'+result.orgnSS[i].id+'" selected>'+result.orgnSS[i].name+'</option>');
								}
							}else{
								if(i==0){
									$('#'+tagId).append('<option value="'+result.orgnSS[i].id+'" selected>'+result.orgnSS[i].name+'</option>');
								}else{
									$('#'+tagId).append('<option value="'+result.orgnSS[i].id+'">'+result.orgnSS[i].name+'</option>');
								}
							}
							
						}
						
						
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
 					$('#'+tagId).chosen('destroy');
 	 				$('#'+tagId+'_chzn').remove();
 	 				$('#'+tagId).removeClass('chzn-done');
 	 				$('#'+tagId).attr('data-placeholder', ' ');
 	 				$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
 				}
				 
			},
			error:function(msg){

			}
		});
	}
	// 查询所有学期，填充到select标签
	,getMajorClasses: function(options) {
		var contextPath = options.contextPath; //项目根路径
		var tagId = options.tagId; //select标签id
		var majorId = options.majorId;//专业id
		var studentNo = options.studentNo;//学号
		var orgClassId = options.orgClassId;//回显值
		var ordered = (null==options.ordered?true:options.ordered);//是否排序，默认排序
		var sortType = (this.stringIsEmpty(options.sortType)?'desc':options.sortType);//排序类型，默认降序
		var sortColumn = options.sortColumn;//排序字段
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var asyncType = (options.asyncType?options.asyncType:false);
		$.ajax({
			url:contextPath+'/common/majorclassSS',
			type:'POST',
			dataType:'json',
			data: {'ordered':ordered, 'sortType':sortType, 'majorId':majorId, 'studentNo':studentNo},
			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();
				$('#'+tagId).append('<option value="">　</option>');
				if (result.success && result.majorclassSS && 0<result.majorclassSS.length)
				{
					for (var i=0; i<result.majorclassSS.length; i++) {
						if (null==orgClassId || ''==orgClassId) {
							$('#'+tagId).append('<option value="'+result.majorclassSS[i].id+'">'+result.majorclassSS[i].name+'</option>');
						} else {
							$('#'+tagId).append('<option value="'+result.majorclassSS[i].id+'" '+(orgSemeId==result.majorclassSS[i].id?'selected':'')+'>'+result.majorclassSS[i].name+'</option>');
						}
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
 					$('#'+tagId).chosen('destroy');
 	 				$('#'+tagId+'_chzn').remove();
 	 				$('#'+tagId).removeClass('chzn-done');
 	 				$('#'+tagId).attr('data-placeholder', ' ');
 	 				$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
 				}
			},
			error:function(msg){

			}
		});
	}

	/** add by xtL on 20190903 start >>>>> */
	// 查询专业下以及所属专业大类下的所有班级
	,getMajorAndSSDLMajorClasses: function(options) {
		var contextPath = options.contextPath; //项目根路径
		var tagId = options.tagId; //select标签id
		var majorId = options.majorId;//专业id
		var studentNo = options.studentNo;//学号
		var orgClassId = options.orgClassId;//回显值
		var ordered = (null==options.ordered?true:options.ordered);//是否排序，默认排序
		var sortType = (this.stringIsEmpty(options.sortType)?'desc':options.sortType);//排序类型，默认降序
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var asyncType = (options.asyncType?options.asyncType:false);
		$.ajax({
			url:contextPath+'/common/majorAndSSDLmajorclassSS',
			type:'POST',
			dataType:'json',
			data: {'ordered':ordered, 'sortType':sortType, 'majorId':majorId, 'studentNo':studentNo},
			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();
				$('#'+tagId).append('<option value="">　</option>');
				if (result.success && result.majorclassSS && 0<result.majorclassSS.length)
				{
					for (var i=0; i<result.majorclassSS.length; i++) {
						if (null==orgClassId || ''==orgClassId) {
							$('#'+tagId).append('<option value="'+result.majorclassSS[i].id+'">'+result.majorclassSS[i].name+'</option>');
						} else {
							$('#'+tagId).append('<option value="'+result.majorclassSS[i].id+'" '+(orgSemeId==result.majorclassSS[i].id?'selected':'')+'>'+result.majorclassSS[i].name+'</option>');
						}
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
					$('#'+tagId).chosen('destroy');
					$('#'+tagId+'_chzn').remove();
					$('#'+tagId).removeClass('chzn-done');
					$('#'+tagId).attr('data-placeholder', ' ');
					$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
				}
			},
			error:function(msg){

			}
		});
	}

	/** add by xtL on 20190903 end <<<<< */

	// 根据班级查询学生，填充到select标签
	,getclassStudents: function(options) {
		var contextPath = options.contextPath; //项目根路径
		var tagId = options.tagId; //select标签id
		var classId = options.classId;//班级id
		var isAll = options.isAll;//是否所有学生（或者是只筛选在校生）
		var orgStudentId = options.orgStudentId;//回显值
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var asyncType = (options.asyncType?options.asyncType:false);
		$.ajax({
			url:contextPath+'/common/classStudentSS',
			type:'POST',
			dataType:'json',
			data: {'classId':classId, 'isAll':isAll},
			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();
				$('#'+tagId).append('<option value="">　</option>');
				if (result.success && result.classStudentSS && 0<result.classStudentSS.length)
				{
					for (var i=0; i<result.classStudentSS.length; i++) {
						if (null==orgStudentId || ''==orgStudentId) {
							$('#'+tagId).append('<option value="'+result.classStudentSS[i].id+'">['+result.classStudentSS[i].xh+'] '+result.classStudentSS[i].xm+'</option>');
						} else {
							$('#'+tagId).append('<option value="'+result.classStudentSS[i].id+'" '+(orgStudentId==result.classStudentSS[i].id?'selected':'')+'>['+result.classStudentSS[i].xh+'] '+result.classStudentSS[i].xm+'</option>');
						}
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
 					$('#'+tagId).chosen('destroy');
 	 				$('#'+tagId+'_chzn').remove();
 	 				$('#'+tagId).removeClass('chzn-done');
 	 				$('#'+tagId).attr('data-placeholder', ' ');
 	 				$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
 				}
			},
			error:function(msg){

			}
		});
	}
	//根据专业和入学年查询班级
	,getMajorClassesByMajorAndNj: function(options) {
		var contextPath = options.contextPath; //项目根路径
		var tagId = options.tagId; //select标签id
		var majorId = options.majorId;//专业id
		var nj= options.nj;//学年
		var njs= options.njs||[];//学年
		var njsflag= options.njsflag?options.njsflag:false;//学年
		var orgn= options.orgn;//学院
		var orgns= options.orgns;//学院
		var orgClassId = options.orgClassId;//回显值
		var ordered = (null==options.ordered?true:options.ordered);//是否排序，默认排序
		var sortType = (this.stringIsEmpty(options.sortType)?'desc':options.sortType);//排序类型，默认降序
		var sortColumn = options.sortColumn;//排序字段
		var autoWidth = (options.autoWidth?options.autoWidth:false);//下拉框自适应宽度（一个字符15px）
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var asyncType = (options.asyncType?options.asyncType:false);//是否格式化chosen
		var appointWidth = (options.appointWidth?options.appointWidth:null);//是否格式化chosen
		var maxWidthLen = 0;
		var clzzSS = [];
		$.ajax({
			url:contextPath+'/common/getClassesByMajorAndXn',
			type:'POST',
			dataType:'json',
			data: {'ordered':ordered, 'sortType':sortType, 'major':majorId, 'nj':nj, 'njs':njs.join(','), 'njsflag':njsflag, 'orgn':orgn, 'sortColumn':sortColumn,orgns:orgns},
			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();
				$('#'+tagId).append('<option value="">　</option>');
				if (result.success && result.majorclassSS && 0<result.majorclassSS.length)
				{
					for (var i=0; i<result.majorclassSS.length; i++) {
                        clzzSS.push({id:result.majorclassSS[i].id, bh:result.majorclassSS[i].bh, bm:result.majorclassSS[i].bm});
						var curOptLen = $.getChineseCharLen(result.majorclassSS[i].name);
 						if (maxWidthLen < curOptLen) {
 							maxWidthLen = curOptLen;
 						}
						if (null==orgClassId || ''==orgClassId) {
							$('#'+tagId).append('<option value="'+result.majorclassSS[i].id+'">'+result.majorclassSS[i].name+'</option>');
						} else {
							$('#'+tagId).append('<option value="'+result.majorclassSS[i].id+'" '+(orgClassId==result.majorclassSS[i].id?'selected':'')+'>'+result.majorclassSS[i].name+'</option>');
						}
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
 					$('#'+tagId).chosen('destroy');
 	 				$('#'+tagId+'_chzn').remove();
 	 				$('#'+tagId).removeClass('chzn-done');
 	 				$('#'+tagId).attr('data-placeholder', ' ');
 	 				$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
 	 				if (autoWidth) {
 	 					var compareWidth = appointWidth?appointWidth:$.chosenDropDefaultWidth();
 	 					if (compareWidth < (maxWidthLen*15/2+50)) {
 	 						$('#'+tagId+'_chzn .chzn-drop').css('width', (maxWidthLen*15/2+50)+'px');
 	 					}
 	 				}
 				}
			},
			error:function(msg){

			}
		});
		return clzzSS;
	}
	,getAllSecTeachSchema: function(options) {
		var contextPath = options.contextPath;	//项目根路径
		var tagId = options.tagId;	//select标签id
		var orgMajorId = options.orgMajorId;	//回显值
		var appendEmptyOpt = options.appendEmptyOpt;	//是否添加空选项
		var emptyOptPosition = options.emptyOptPosition;	//空选项位置
		var exclude = options.exclude;	//是否剔除选项
		var excludeSS = options.excludeSS;	//剔除选项
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var asyncType = (options.asyncType?options.asyncType:false);
		$.ajax({
			url:contextPath+'/common/secTeachSchemas',
			type:'POST',
			dataType:'json',
			data: {'ordered':true, 'sortType':'asc'},
			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();

					$('#'+tagId).append('<option value=""> </option>');

				if (result.success && result.majorSS && 0<result.majorSS.length)
				{
					for (var i=0; i<result.majorSS.length; i++) {
						if (null==orgMajorId || ''==orgMajorId) {
							$('#'+tagId).append('<option value="'+result.majorSS[i].id+'">'+result.majorSS[i].name+'</option>');
						} else {
							$('#'+tagId).append('<option value="'+result.majorSS[i].id+'" '+(orgMajorId==result.majorSS[i].id?'selected':'')+'>'+result.majorSS[i].name+'</option>');
						}
					}
					if (appendEmptyOpt && 'tail' == emptyOptPosition) {
						$('#' + tagId).append('<option value=""></option>');
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
					$('#'+tagId).chosen('destroy');
					$('#'+tagId+'_chzn').remove();
					$('#'+tagId).removeClass('chzn-done');
					$('#'+tagId).attr('data-placeholder', ' ');
					$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
				}
			},
			error:function(msg){

			}
		});
	}
	,getAllSecClasses: function(options) {
		var contextPath = options.contextPath;	//项目根路径
		var tagId = options.tagId;	//select标签id
		var orgMajorId = options.orgMajorId;	//回显值
		var appendEmptyOpt = options.appendEmptyOpt;	//是否添加空选项
		var emptyOptPosition = options.emptyOptPosition;	//空选项位置
		var exclude = options.exclude;	//是否剔除选项
		var excludeSS = options.excludeSS;	//剔除选项
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var schema=options.schema;
		var asyncType = (options.asyncType?options.asyncType:false);
		var customize = options.customize;
		$.ajax({
			url:contextPath+'/common/secClasses',
			type:'POST',
			dataType:'json',
			data: {
				//'ordered':true,
				'sortType':'asc','schema':schema,'customize':customize},
			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();
				if (appendEmptyOpt && 'top' == emptyOptPosition) {
					$('#'+tagId).append('<option value=""></option>');
				}
				if (result.success && result.secClassSS && 0<result.secClassSS.length)
				{
					for (var i=0; i<result.secClassSS.length; i++) {
						if (null==orgMajorId || ''==orgMajorId) {
							$('#'+tagId).append('<option value="'+result.secClassSS[i].id+'">'+result.secClassSS[i].name+'</option>');
						} else {
							$('#'+tagId).append('<option value="'+result.secClassSS[i].id+'" '+(orgMajorId==result.secClassSS[i].id?'selected':'')+'>'+result.secClassSS[i].name+'</option>');
						}
					}
					if (appendEmptyOpt && 'tail' == emptyOptPosition) {
						$('#' + tagId).append('<option value=""></option>');
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
					$('#'+tagId).chosen('destroy');
					$('#'+tagId+'_chzn').remove();
					$('#'+tagId).removeClass('chzn-done');
					$('#'+tagId).attr('data-placeholder', ' ');
					$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
				}
			},
			error:function(msg){

			}
		});
	}
	,getProvinces: function(options) {
		var contextPath = options.contextPath;	//项目根路径
		var tagId = options.tagId;	//select标签id
		var orgProvince = options.orgProvince;	//回显值
		var appendEmptyOpt = options.appendEmptyOpt;	//是否添加空选项
		var emptyOptPosition = options.emptyOptPosition;	//空选项位置
		var exclude = options.exclude;	//是否剔除选项
		var excludeSS = options.excludeSS;	//剔除选项
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var asyncType = (options.asyncType?options.asyncType:false);
		$.ajax({
			url:contextPath+'/common/provinces',
			type:'POST',
			dataType:'json',
			data: {'ordered':true, 'sortType':'asc'},
			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();
				if (appendEmptyOpt && 'top' == emptyOptPosition) {
					$('#'+tagId).append('<option value=""></option>');
				}
				if (result.success && result.provinces && 0<result.provinces.length)
				{
					for (var i=0; i<result.provinces.length; i++) {
						if (null==orgProvince || ''==orgProvince) {
							$('#'+tagId).append('<option value="'+result.provinces[i].ID+'">'+result.provinces[i].NAME+'</option>');
						} else {
							$('#'+tagId).append('<option value="'+result.provinces[i].ID+'" '+(orgProvince==result.provinces[i].ID?'selected':'')+'>'+result.provinces[i].NAME+'</option>');
						}
					}
					if (appendEmptyOpt && 'tail' == emptyOptPosition) {
						$('#' + tagId).append('<option value=""></option>');
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
					$('#'+tagId).chosen('destroy');
					$('#'+tagId+'_chzn').remove();
					$('#'+tagId).removeClass('chzn-done');
					$('#'+tagId).attr('data-placeholder', ' ');
					$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
				}
			},
			error:function(msg){

			}
		});
	}
	,getCitys: function(options) {
		var contextPath = options.contextPath;	//项目根路径
		var tagId = options.tagId;	//select标签id
		var orgCityId = options.orgCityId;	//回显值
		var appendEmptyOpt = options.appendEmptyOpt;	//是否添加空选项
		var emptyOptPosition = options.emptyOptPosition;	//空选项位置
		var exclude = options.exclude;	//是否剔除选项
		var excludeSS = options.excludeSS;	//剔除选项
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var provinceId=options.provinceId;
		var asyncType = (options.asyncType?options.asyncType:false);
		$.ajax({
			url:contextPath+'/common/citys',
			type:'POST',
			dataType:'json',
			data: {'ordered':true, 'sortType':'asc','provinceId':provinceId},
			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();
				if (appendEmptyOpt && 'top' == emptyOptPosition) {
					$('#'+tagId).append('<option value=""></option>');
				}
				if (result.success && result.citys && 0<result.citys.length)
				{
					for (var i=0; i<result.citys.length; i++) {
						if (null==orgCityId || ''==orgCityId) {
							$('#'+tagId).append('<option value="'+result.citys[i].ID+'">'+result.citys[i].NAME+'</option>');
						} else {
							$('#'+tagId).append('<option value="'+result.citys[i].ID+'" '+(orgCityId==result.citys[i].ID?'selected':'')+'>'+result.citys[i].NAME+'</option>');
						}
					}
					if (appendEmptyOpt && 'tail' == emptyOptPosition) {
						$('#' + tagId).append('<option value=""></option>');
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
					$('#'+tagId).chosen('destroy');
					$('#'+tagId+'_chzn').remove();
					$('#'+tagId).removeClass('chzn-done');
					$('#'+tagId).attr('data-placeholder', ' ');
					$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
				}
			},
			error:function(msg){

			}
		});
	}
	,getBuildingInfo: function(options) {
		var contextPath = options.contextPath;	//项目根路径
		var tagId = options.tagId;	//select标签id
		var orgCityId = options.orgCityId;	//回显值
		var appendEmptyOpt = options.appendEmptyOpt;	//是否添加空选项
		var emptyOptPosition = options.emptyOptPosition;	//空选项位置
		var exclude = options.exclude;	//是否剔除选项
		var excludeSS = options.excludeSS;	//剔除选项
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var provinceId=options.provinceId;
		var asyncType = (options.asyncType?options.asyncType:false);
		$.ajax({
			url:contextPath+'/common/buildings',
			type:'POST',
			dataType:'json',
			data: {'ordered':true, 'sortType':'asc'},
			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();
				if (appendEmptyOpt && 'top' == emptyOptPosition) {
					$('#'+tagId).append('<option value=""></option>');
				}
				if (result.success && result.buildings && 0<result.buildings.length)
				{
					for (var i=0; i<result.buildings.length; i++) {
						if (null==orgCityId || ''==orgCityId) {
							$('#'+tagId).append('<option value="'+result.buildings[i].ID+'">'+result.buildings[i].NAME+'</option>');
						} else {
							$('#'+tagId).append('<option value="'+result.buildings[i].ID+'" '+(orgCityId==result.buildings[i].ID?'selected':'')+'>'+result.buildings[i].NAME+'</option>');
						}
					}
					if (appendEmptyOpt && 'tail' == emptyOptPosition) {
						$('#' + tagId).append('<option value=""></option>');
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
					$('#'+tagId).chosen('destroy');
					$('#'+tagId+'_chzn').remove();
					$('#'+tagId).removeClass('chzn-done');
					$('#'+tagId).attr('data-placeholder', ' ');
					$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
				}
			},
			error:function(msg){

			}
		});
	}
	// 更新单选select chosen
	,refreshSingleChosen: function(options) {
		var tagId = options.tagId;
		var newValue = options.newValue;
		$('#'+tagId).val(newValue);
		// chosen重载>>>>>>>>>>>
		$('#'+tagId).chosen('destroy');
		$('#'+tagId+'_chzn').remove();
		$('#'+tagId).removeClass('chzn-done');
		$('#'+tagId).attr('data-placeholder', ' ');
		$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
		// <<<<<<<<<
	}
	// 更新多选select chosen
	,refreshMultiChosen: function(options) {
		var tagId = options.tagId;
		var newValue = options.newValue;
		if ($.stringIsEmpty(newValue)) {
			return;
		}
		var values = newValue.split(",")||[];
		$("#"+tagId).find("option").each(function(){
			for(var i=0;i<values.length;i++) {
				if($(this).val() == values[i]){
					$(this).attr("selected", true);
				}
			}
		})
		$("#"+tagId).trigger("liszt:updated");
	}
	// 单选/复选框格式化
	,formatRadioAndCheckbox: function() {
		$("input:checkbox").uniform();
	    $("input:radio").uniform();
	}
	// 初始化下拉多选
	,formatMultipleSelect: function() {
		$('select[multiple="multiple"]').multiselect({
	        nonSelectedText: "请选择",
	        allSelectedText: "全选",
	        nSelectedText: '选中',
	        filterPlaceholder: '搜索',
	        numberDisplayed: 6,//选中大于6个表现显示选中数量
	        buttonWidth: '220px',
	        enableFiltering: true,
	        templates: {
	            button: "<button type='button' class='multiselect dropdown-toggle'   data-toggle='dropdown' style='margin-bottom: 0px'><span class='multiselect-selected-text'></span> <b class='caret'></b></button>",
	            filterClearBtn: ""
	        }, onChange: function (element) {
	            $(element).parent().blur();
	        }
	    });
	}
	// 获取学年
	,getLearnYear: function(options) {
		var tagId = options.tagId;
		var begin = options.begin?options.begin:(this.getYear()-14);
		var end = options.end?options.end:(this.getYear()+2);
		var appendEmptyOpt = options.appendEmptyOpt;	//是否添加空选项
		var emptyOptPosition = options.emptyOptPosition;	//空选项位置
		var emptyOptVal = options.emptyOptVal?options.emptyOptVal:'';				//空option值
		var emptyOptTxt = options.emptyOptTxt?options.emptyOptTxt:'　';				//空option文本
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		$('#'+tagId).empty();
		if (appendEmptyOpt && 'top' == emptyOptPosition) {
			$('#'+tagId).append('<option value="'+emptyOptVal+'">'+emptyOptTxt+'</option>');
		}
		for (var i=end; i>=begin; i--) {
			$('#'+tagId).append('<option value="'+i+'">'+i+'</option>');
		}
		if (appendEmptyOpt && 'tail' == emptyOptPosition) {
			$('#' + tagId).append('<option value="'+emptyOptVal+'">'+emptyOptTxt+'</option>');
		}
		if (chosenFormat && 0<$('#'+tagId+' option').length) {
			$('#'+tagId).chosen('destroy');
			$('#'+tagId+'_chzn').remove();
			$('#'+tagId).removeClass('chzn-done');
			$('#'+tagId).attr('data-placeholder', ' ');
			$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
		}
	}
	,getCountrys: function(options) {
		var contextPath = options.contextPath;	//项目根路径
		var tagId = options.tagId;	//select标签id
		var orgCountry = options.orgCountry;	//回显值
		var appendEmptyOpt = options.appendEmptyOpt;	//是否添加空选项
		var emptyOptPosition = options.emptyOptPosition;	//空选项位置
		var exclude = options.exclude;	//是否剔除选项
		var excludeSS = options.excludeSS;	//剔除选项
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var cityId=options.cityId;
		$.ajax({
			url:contextPath+'/common/countrys',
			type:'POST',
			dataType:'json',
			data: {'ordered':true, 'sortType':'asc','city':cityId},
			async: false,
			success:function(result){
				$('#'+tagId).empty();
				if (appendEmptyOpt && 'top' == emptyOptPosition) {
					$('#'+tagId).append('<option value=""></option>');
				}
				if (result.success && result.countrys && 0<result.countrys.length)
				{
					for (var i=0; i<result.countrys.length; i++) {
						if (null==orgCountry || ''==orgCountry) {
							$('#'+tagId).append('<option value="'+result.countrys[i].ID+'">'+result.countrys[i].NAME+'</option>');
						} else {
							$('#'+tagId).append('<option value="'+result.countrys[i].ID+'" '+(orgCountry==result.countrys[i].ID?'selected':'')+'>'+result.countrys[i].NAME+'</option>');
						}
					}
					if (appendEmptyOpt && 'tail' == emptyOptPosition) {
						$('#' + tagId).append('<option value=""></option>');
					}
				}
			},
			error:function(msg){

			}
		});
		if (chosenFormat && 0<$('#'+tagId+' option').length) {
			$('#'+tagId).chosen('destroy');
			$('#'+tagId+'_chzn').remove();
			$('#'+tagId).removeClass('chzn-done');
			$('#'+tagId).attr('data-placeholder', ' ');
			$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
		}
	}
	,getAllTeachers: function(options) {
		var contextPath = options.contextPath;	//项目根路径
		var tagId = options.tagId;	//select标签id
		var orgTeacher = options.orgTeacher;	//回显值
		var appendEmptyOpt = options.appendEmptyOpt;	//是否添加空选项
		var emptyOptPosition = options.emptyOptPosition;	//空选项位置
		var exclude = options.exclude;	//是否剔除选项
		var excludeSS = options.excludeSS;	//剔除选项
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var isMulti = options.isMulti;
		var textType = options.textType;
		var isAcad31 = options.isAcad31?options.isAcad31:false;
		var techSS = [];
		$.ajax({
			url:contextPath+'/common/allTeachers',
			type:'POST',
			dataType:'json',
			data: {'ordered':true, 'sortType':'asc', textType:textType, isAcad31:isAcad31},
			// async: false,
			success:function(result){
				$('#'+tagId).empty();
				if (appendEmptyOpt && 'top' == emptyOptPosition) {
					$('#'+tagId).append('<option value=""></option>');
				}
				if (result.success && result.teacherSS && 0<result.teacherSS.length)
				{
					for (var i=0; i<result.teacherSS.length; i++) {
						techSS.push({id:result.teacherSS[i].id, gh:result.teacherSS[i].gh, xm:result.teacherSS[i].xm});
						if (null==orgTeacher || ''==orgTeacher) {
							$('#'+tagId).append('<option value="'+result.teacherSS[i].id+'">'+result.teacherSS[i].name+'</option>');
						} else {
							$('#'+tagId).append('<option value="'+result.teacherSS[i].id+'" '+(orgTeacher==result.teacherSS[i].id?'selected':'')+'>'+result.teacherSS[i].name+'</option>');
						}
					}
					if (appendEmptyOpt && 'tail' == emptyOptPosition) {
						$('#' + tagId).append('<option value=""></option>');
					}
				}
			},
			error:function(msg){

			}
		});
		if (chosenFormat && 0<$('#'+tagId+' option').length) {
			$('#'+tagId).chosen('destroy');
			$('#'+tagId+'_chzn').remove();
			$('#'+tagId).removeClass('chzn-done');
			$('#'+tagId).attr('data-placeholder', ' ');
			$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
		}
		return techSS;
	}
	/** add by xtL on 20191101 */
	,getCourseTableTeachers: function(options) {
		var contextPath = options.contextPath;	//项目根路径
		var tagId = options.tagId;	//select标签id
		var orgTeacher = options.orgTeacher;	//回显值
		var appendEmptyOpt = options.appendEmptyOpt;	//是否添加空选项
		var emptyOptPosition = options.emptyOptPosition;	//空选项位置
		var exclude = options.exclude;	//是否剔除选项
		var excludeSS = options.excludeSS;	//剔除选项
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var isMulti = options.isMulti;
		var textType = options.textType;
		var sem = options.sem;
		var isAcad31 = options.isAcad31?options.isAcad31:false;
		var techSS = [];
		$.ajax({
			url:contextPath+'/common/allCourseTableTeachers',
			type:'POST',
			dataType:'json',
			data: {'ordered':true, 'sortType':'asc', textType:textType,sem:sem, isAcad31:isAcad31},
			// async: false,
			success:function(result){
				$('#'+tagId).empty();
				if (appendEmptyOpt && 'top' == emptyOptPosition) {
					$('#'+tagId).append('<option value=""></option>');
				}
				if (result.success && result.teacherSS && 0<result.teacherSS.length)
				{
					for (var i=0; i<result.teacherSS.length; i++) {
						techSS.push({id:result.teacherSS[i].id, gh:result.teacherSS[i].gh, xm:result.teacherSS[i].xm});
						if (null==orgTeacher || ''==orgTeacher) {
							$('#'+tagId).append('<option value="'+result.teacherSS[i].id+'">'+result.teacherSS[i].name+'</option>');
						} else {
							$('#'+tagId).append('<option value="'+result.teacherSS[i].id+'" '+(orgTeacher==result.teacherSS[i].id?'selected':'')+'>'+result.teacherSS[i].name+'</option>');
						}
					}
					if (appendEmptyOpt && 'tail' == emptyOptPosition) {
						$('#' + tagId).append('<option value=""></option>');
					}
				}
			},
			error:function(msg){

			}
		});
		if (chosenFormat && 0<$('#'+tagId+' option').length) {
			$('#'+tagId).chosen('destroy');
			$('#'+tagId+'_chzn').remove();
			$('#'+tagId).removeClass('chzn-done');
			$('#'+tagId).attr('data-placeholder', ' ');
			$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
		}
		return techSS;
	}
	,loadStaticSourceServer: function () {
		var staticSorce;
		$.ajax({
			url:contextPath+'/redisCache/sysparam',
			type:'POST',
			dataType:'json',
			data:{paramName:'static_resource_server'},
			async:false,
			success:function(data){
				if (data.success) {
					staticSorce = data.paramValue;
				}
			}
		});
		return staticSorce;
	}
	,loadSysParam: function (options) {
		var contextPath = options.contextPath;	//项目根路径
		var paramName = options.paramName;	//参数代码
		var staticSorce;
		$.ajax({
			url:contextPath+'/redisCache/sysparam',
			type:'POST',
			dataType:'json',
			data:{paramName:paramName},
			async:false,
			success:function(data){
				if (data.success) {
					staticSorce = data.paramValue;
				}
			}
		});
		return staticSorce;
	}
	,loadByUrl: function(url) {
		var d = "";
		$.ajax({
			url:url,
			dataType:'json',
			type:'post',
			async:false,
			success:function(data){
				d = data;
			}
		})
		return d;
	}
	,setDicToSelectGrp: function(dics,grpDescs,element,autoWidth,includeOtherSchool) {
//		var optHtml = '';
//		for (var i=0; i<dics.length; i++) {
//			optHtml = optHtml+'<optgroup label="'+grpDescs[i]+'">';
//			for(var j = 0;j<dics[i].length;j++){
//				optHtml = optHtml+'<option value="'+dics[i][j].ID+'">'+dics[i][j].TEXT+'</option>';
//			}
//			optHtml = optHtml+'</optgroup>';
//		}
//		$("#"+element).append(optHtml);
//		$("#"+element).chosen();
		includeOtherSchool = (null==includeOtherSchool?true:includeOtherSchool);
		var optHtml = '';
		var maxWidthLen = 0;
		for(var i = 0;i<dics.length;i++){
			optHtml = optHtml+'<optgroup label="'+grpDescs[i]+'">';
			for (var j=0; j<dics[i].length; j++) {
				if (!includeOtherSchool && 1==dics[i][j].WX) {
					continue;
				}
				var curOptLen = $.getChineseCharLen(dics[i][j].TEXT);
				if (maxWidthLen < curOptLen) {
					maxWidthLen = curOptLen;
				}
				optHtml = optHtml+'<option value="'+dics[i][j].ID+'">'+dics[i][j].TEXT+'</option>';
			}
			optHtml = optHtml+'</optgroup>';
		}
		$("#"+element).append(optHtml);
		$("#"+element).chosen();
		if ('auto' == autoWidth) {
			if ($.chosenDropDefaultWidth() < (maxWidthLen*15/2+50)) {
				$('#'+element+'_chzn .chzn-drop').css('width', (maxWidthLen*15/2+50)+'px');
			}
		}
	}
	,chosenRefresh: function(tagId, refreshVal) {
		if (refreshVal) {
			$('#'+tagId).val(refreshVal);
		} else {
			$('#'+tagId).val('');
		}
		$('#'+tagId).chosen('destroy');
		$('#'+tagId+'_chzn').remove();
		$('#'+tagId).removeClass('chzn-done');
		$('#'+tagId).attr('data-placeholder', ' ');
		$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
	}
	,chosenRefreshSimple: function(tagId) {
		$('#'+tagId).trigger('liszt:updated');
	}
	,chosenReWidth: function(options) {
		var tagId = options.tagId;
		var appiontMinWidth = options.appiontMinWidth;
		var maxWidthLen = 0;
		$('#'+tagId+' option').each(function(){
			var curOptLen = $.getChineseCharLen($(this).text());
			if (maxWidthLen < curOptLen) {
				maxWidthLen = curOptLen;
			}
		});
		if (!appiontMinWidth) {
			appiontMinWidth = $.chosenDropDefaultWidth();
		}
		if (appiontMinWidth < (maxWidthLen*15/2+50)) {
			$('#'+tagId+'_chzn .chzn-drop').css('width', (maxWidthLen*15/2+50)+'px');
			$('#'+tagId+'_chzn .chzn-search input').css('width', (maxWidthLen*15/2+50-60)+'px');
		}
	}
	,chosenFormat: function (tagId, maxWidthLen) {
		$('#'+tagId).chosen('destroy');
		$('#'+tagId+'_chzn').remove();
		$('#'+tagId).removeClass('chzn-done');
		$('#'+tagId).attr('data-placeholder', ' ');
		$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
		if (maxWidthLen) {
			$('#'+tagId+'_chzn .chzn-drop').css('width', (maxWidthLen*15/2+50)+'px');
		}
	}
	// 指定下拉范围，并指定默认选项
	,fixedSelectScope: function(options){
		var tagId = options.tagId;
		var optionsScope = options.optionsScope;
		var defaultSelected = options.defaultSelected;
		var defaultSelectedId = null;
		var retainEmpty = options.retainEmpty?options.retainEmpty:false;
		if (optionsScope) {
			var optioinsScopeStr = optionsScope.join(',');
			// $('#'+tagId+' option').each(function(){
			// 	if (-1 == optioinsScopeStr.indexOf($(this).text())) {
			// 		$(this).remove();
			// 	}
			// });
			var optSize = $('#'+tagId+' option').length;
			for (var i=optSize-1; i>=0; i--) {
				if (defaultSelected == $('#'+tagId+' option:eq('+i+')').text()) {
					defaultSelectedId = $('#'+tagId+' option:eq('+i+')').val();
				}
				if (-1 == optioinsScopeStr.indexOf($('#'+tagId+' option:eq('+i+')').text())) {
					if (retainEmpty && $.stringIsEmpty($('#'+tagId+' option:eq('+i+')').val())) {
						continue;
					}
					$('#'+tagId+' option:eq('+i+')').remove();
				}
			}
		}
		if (defaultSelectedId) {
			$('#'+tagId).val(defaultSelectedId);
		}
		$('#'+tagId).trigger('liszt:updated');
	}
	// yyyy-MM-dd regex
	,dateFormat_yyyy_MM_dd: new RegExp("^[1-2]\\d{3}-(0?[1-9]||1[0-2])-(0?[1-9]||[1-2][0-9]||3[0-1])$")
	// 正整数正则
	,regex_positive_digital: new RegExp("^(0|[1-9][0-9]*)$")
	// 实数正则
	,regex_decimal: new RegExp("^-?\\d+(\\.\\d+)?$")
	// 汉字正则
//	,regex_chinese: new RegExp("[\\u4E00-\\u9FFF]+","g")
	,regex_chinese: /^[\u4e00-\u9fa5]+$/
	// 获取当前年
	,getYear: function() {
		return new Date().getFullYear();
	}
	// 获取当前月（fill决定是否把1-9月补充为01-09月）
	,getMonth: function(fill) {
		var month = new Date().getMonth()+1;
		if (fill && 9>=parseInt(month)) {
			month = '0'+month;
		}
		return month;
	}
	// 获取当前日（fill决定是否把1-9日补充为01-09日）
	,getDay: function(fill) {
		var day = new Date().getDate();
		if (fill && 9>=parseInt(day)) {
			day = '0'+day;
		}
		return day;
	}
	// 获取yyyy-MM-dd格式日期
	,getDate: function(fill) {
		var year = new Date().getFullYear();
		var month = new Date().getMonth()+1;
		var day = new Date().getDate();
		var date = '';
		if (fill) {
			date = year+(9>=parseInt(month)?'-0'+month:'-'+month)+(9>=parseInt(day)?'-0'+day:'-'+day);
		} else {
			date = year+'-'+month+'-'+day;
		}
		return date;
	}
	// 获取yyyy-MM-dd HH:mm:ss格式日期
	,getDateHour: function(fill) {
		var curDate = new Date();
		var year = curDate.getFullYear();
		var month = curDate.getMonth()+1;
		var day = curDate.getDate();
		var hours = curDate.getHours();
		var date = '';
		if (fill) {
			date = year+(9>=parseInt(month)?'-0'+month:'-'+month)+(9>=parseInt(day)?'-0'+day:'-'+day)
				+(9>=parseInt(hours)?' 0'+hours:' '+hours);
		} else {
			date = year+'-'+month+'-'+day+' '+hours;
		}
		return date;
	}
	// 获取yyyy-MM-dd HH:mm:ss格式日期
	,getDateSec: function(fill) {
		var curDate = new Date();
		var year = curDate.getFullYear();
		var month = curDate.getMonth()+1;
		var day = curDate.getDate();
		var hours = curDate.getHours();
		var minutes = curDate.getMinutes();
		var seconds = curDate.getSeconds();
		var date = '';
		if (fill) {
			date = year+(9>=parseInt(month)?'-0'+month:'-'+month)+(9>=parseInt(day)?'-0'+day:'-'+day)
				+(9>=parseInt(hours)?' 0'+hours:' '+hours)+(9>=parseInt(minutes)?':0'+minutes:':'+minutes)+(9>=parseInt(seconds)?':0'+seconds:':'+seconds);
		} else {
			date = year+'-'+month+'-'+day+' '+hours+":"+minutes+":"+seconds;
		}
		return date;
	}

	// 日期格式化，yyyy-MM-dd截取yyyy
	,getDateYear: function(date) {
		var dateYear = '';
		var r = this.dateFormat_yyyy_MM_dd;
		if (10 < date.length) {
			date = date.substring(0, 10);
		}
		if (r.test(date)) {
			dateYear = date.substring(0, 4);
		}
		return dateYear;
	}
	// 日期格式化，yyyy-MM-dd截取MM（split决定是否把01-09月截取为1-9月）
	,getDateMonth: function(date, split) {
		var dateMonth = '';
		var r = this.dateFormat_yyyy_MM_dd;
		if (10 < date.length) {
			date = date.substring(0, 10);
		}
		if (r.test(date)) {
			dateMonth = date.substring(5, 7);
		}
		if (split) {
			dateMonth = parseInt(dateMonth);
		}
		return dateMonth;
	}
	// 日期格式化，yyyy-MM-dd截取yyyy（split决定是否把01-09日截取为1-9日）
	,getDateDay: function(date, split) {
		var dateDay = '';
		var r = this.dateFormat_yyyy_MM_dd;
		if (10 < date.length) {
			date = date.substring(0, 10);
		}
		if (r.test(date)) {
			dateDay = date.substring(8, 10);
		}
		if (split) {
			dateDay = parseInt(dateDay);
		}
		return dateDay;
	}
	// yyyy-MM-dd日期比较大小，isSysDate为true：compDate使用系统当前日期
	,compareDate: function(ognlDate, compDate, isSysDate) {
		isSysDate = (null==isSysDate?false:isSysDate);
		if (isSysDate) {
			compDate = this.getDate(true);
		}
		return ognlDate.localeCompare(compDate);
	}

	// 获取中英文混合字符串中，字符和汉字个数
	,getStringLength: function(orgValue) {
		var len = {enLen:0, zhLen:0, digLen:0};
		if (orgValue.match(/[^ -~]/g) == null) {
			len.enLen = orgValue.length;
		} else {
			len.zhLen = (null==orgValue.match(/[^ -~]/g)?0:orgValue.match(/[^ -~]/g).length);
			len.digLen = (null==orgValue.match(/[0-9]/g)?0:orgValue.match(/[0-9]/g).length);
			len.enLen = orgValue.length-len.zhLen-len.digLen;
		}
		return len;
	}
	// span下划线空白补充&nbsp;，补充规则：170px==26个&nbsp;，一个字符等于13/7个&nbsp;，一个汉字27/8个&nbsp;，一个数字2个&nbsp;，剩余前后平分补充&nbsp;，超过170px长度，改变span宽度
	,spanUnderLineFormat: function(orgValue, fixWidth, fixWidthCnt) {
		var formatResult = {scope:'inner', result:'', reWidth:0, increase:0};
		var len = this.getStringLength(orgValue);
		var spaceLen = len.enLen*13/7 + len.zhLen*27/8 + len.digLen*2;
		var spaceLenEq = Math.round(spaceLen);
		if (spaceLenEq > fixWidthCnt) {
			formatResult.scope = 'outer';
			var lessCnt = spaceLenEq - fixWidthCnt;
			formatResult.increase = parseInt(fixWidth/fixWidthCnt*lessCnt)+1;
			formatResult.reWidth = fixWidth + formatResult.increase;
		} else {
			var fillCnt = fixWidthCnt - spaceLenEq;
			var prexFillCnt = parseInt(fillCnt/2);
			var tailFillCnt = fillCnt - prexFillCnt;
			formatResult.result = this.constructSpaceGroup(prexFillCnt) + orgValue + this.constructSpaceGroup(tailFillCnt);
		}
		return formatResult;
	}
	// 构造多个&nbsp;
	,constructSpaceGroup: function(count) {
		var spaceGrp = '';
		for (var i=0; i<count; i++) {
			spaceGrp += '&nbsp;';
		}
		return spaceGrp;
	}

	// 转义字符‘\’转成‘\\’或‘/’;
	,tranTo: function(str,type) {
		//这里第二个参数g表示全部都替换，如果换成是i或不写则表示替换第一个。
		if(type == 1){
			str = str.replace(/\\/g,"/")
		}else if(type == 0){
			str = str.replace(/\\/g,"\\\\")
		}
		return str;
	}

	// 判断字符串是否为空
	,stringIsEmpty: function(orgValue) {
		if (null==orgValue || ''==orgValue) {
			return true;
		} else {
			return false;
		}
	}
	,stringDefault: function(orgValue, defaultVal) {
		if (!this.stringIsEmpty(orgValue)) {
			return orgValue;
		} else {
			defaultVal = defaultVal||'';
			return defaultVal;
		}
	}
	// 去掉字符串左边空格20170612
	,trimL: function(orgValue) {
		var fnlValue = '';
		if (this.stringIsEmpty(orgValue)) {
			return fnlValue;
		} else {
			fnlValue = orgValue.replace(/(^\s*)/g, "");
		}
		return fnlValue;
	}
	// 去掉字符串右边空格20170612
	,trimR: function(orgValue) {
		var fnlValue = '';
		if (this.stringIsEmpty(orgValue)) {
			return fnlValue;
		} else {
			fnlValue = orgValue.replace(/(\s*$)/g, "");
		}
		return fnlValue;
	}
	// 去掉字符串两边空格20170612
	,trimLR: function(orgValue) {
		var fnlValue = '';
		if (this.stringIsEmpty(orgValue)) {
			return fnlValue;
		} else {
			fnlValue = orgValue.replace(/(^\s*)/g, "").replace(/(\s*$)/g, "");
//			fnlValue = fnlValue.replace(/(\s*$)/g, "");
		}
		return fnlValue;
	}

	// 整数正则表达式校验20170615
	,isPositiveDigital: function(orgValue) {
		return this.regex_positive_digital.test(orgValue);
	}
	,isDecimal: function(orgValue) {
		return this.regex_decimal.test(orgValue);
	}
	// 汉字正则表达式校验
	,isChineseChar: function(orgValue) {
		return this.regex_chinese.test(orgValue);
	}
	,getChineseCharLen: function(oglValue) {
		var len = 0;
		if (!this.stringIsEmpty(oglValue)) {
			for (var i=0; i<oglValue.length; i++) {
				var tmp = oglValue.charAt(i);
				if (this.isChineseChar(oglValue.charAt(i)) || '（'==oglValue.charAt(i) || '）'==oglValue.charAt(i)) {
					len += 2;
				} else {
					len += 1;
				}
			}
		}
		return len;
	}
	,chosenDropDefaultWidth: function() {
		return 218;
	}
	,isPhoneNo: function(numValue) {
//		var pattern = /^1[34578]\d{9}$/;
		var pattern = /^(13[0-9]|14[579]|15[0-3,5-9]|16[6]|17[0135678]|18[0-9]|19[89])\d{8}$/;
	    return pattern.test(numValue);
	}
	,isIDCard: function(idValue) {
		var pattern = /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/;
		return pattern.test(idValue);
	}
	,replaceSpace: function (oglValue) {
		oglValue = oglValue||'';
		return oglValue.replace(/\s+/g,"");
	}
	// 基础任务模块-根据taskId删除任务20170613
	,deleteBaseTask: function(taskId, callbackFun) {
		if (confirm("数据删除不可恢复，请确认！")) {
			$.ajax({
				url:'${sessionScope.contextPath}/basetask/deletetask',
	 			type:'POST',
	 			dataType:'json',
	 			data:{'taskId':taskId},
	 			success:function(result){
	 				if (result.success)
	 				{
	 					if (null != callbackFun) {
	 						var callback = eval(callbackFun);
							callback();
	 					}
	 				}
	 			},
				error:function(msg){

				}
			});
		}
	}
	// 查看课程大纲、教学日历、教学概述
	,viewCourseMaterial: function(options) {
		var courseCode = options.courseCode;
		var type = options.type?options.type:1;
		var tagId = options.tagId;
		var contextPath = options.contextPath;
		$.ajax({
            // url : contextPath+'/course/onlineViewNew',
            url : contextPath+'/course/onlineViewNewBySftp',
            type :'POST',
            dataType : 'json',
            data : {courseCode:courseCode, type:type},
            success:function(result){
                if(!result.success){
                    $("#"+tagId+" .content").html(result.msg);
                }else{
                    $("#"+tagId+" .content").html(result.content);
                }
                var modalWidth = $("#"+tagId).width();
                var left = "-" + parseInt(modalWidth) / 2 + "px";
                $("#"+tagId).modal("show").css({"margin-left":left});
            }
        });
	}

	// 查看课程大纲、教学日历、教学概述(使用SFTP) add by xtL on 20200225
	,viewCourseMaterialBySftp: function(options) {
		var flag=true;
		var courseCode = options.courseCode;
		var type = options.type?options.type:1;
		var tagId = options.tagId;
		var contextPath = options.contextPath;
		$.ajax({
			url : contextPath+'/course/onlineViewNewBySftp',
			type :'POST',
			dataType : 'json',
			data : {courseCode:courseCode, type:type},
			success:function(result){
				if(!result.success){
					$("#"+tagId+" .content").html(result.msg);
				}else{
					if (result.type != null && result.type === 'pdf') {
						flag=false;
						window.open('/view/'+result.content);
					}else if (result.type != null &&result.fileViewType != null &&result.fileViewType ==='kkFile' &&( result.type === 'doc'||result.type === 'docx')){
						flag=false;
						window.open(result.kkFileUrl+'onlinePreview?url='+encodeURIComponent( window.btoa( result.webUrl+'courseTeacherOutline/downloadfileKKview?secret='+result.secret+'&directory='+result.directory+'&downloadFile='+result.downloadFile+'&fullfilename='+result.downloadFile)));
					}else {
						$("#"+tagId+" .content").html(result.content);
					}

				}

				if (flag){
					var modalWidth = $("#"+tagId).width();
					var left = "-" + parseInt(modalWidth) / 2 + "px";
					$("#"+tagId).modal("show").css({"margin-left":left});
				}

			}
		});
	}

	// 打印课程大纲、教学日历、教学概述
	,printCourseMaterial: function(options) {
		var courseCode = options.courseCode;
		var type = options.type?options.type:1;
		var tagId = options.tagId;
		var contextPath = options.contextPath;
		window.open(contextPath+'/course/printViewNew/'+courseCode+'/'+type, '_blank');
	}
	// 单页面跳转初始化
	,initFullPage: function(rootTagId, barName,showOther,showMe)
	{
		runPage = new FullPage({
			id : rootTagId,                            // id of contain
			slideTime : 800,                               // time of slide
			continuous : false,                            // create an infinite feel with no endpoints
			effect : {                                     // slide effect
		        	transform : {
		        		translate : 'Y',				   // 'X'|'Y'|'XY'|'none'
		        		scale : [.1, 1],				   // [scalefrom, scaleto]
		        		rotate : [0, 0]				       // [rotatefrom, rotateto]
		        	},
		        	opacity : [0, 1]                       // [opacityfrom, opacityto]
		    	},
			mode : 'touch,nav:'+barName,               // mode of fullpage
			easing : 'ease',                                // easing('ease','ease-in','ease-in-out' or use cubic-bezier like [.33, 1.81, 1, 1];
			showMe : showMe,
			showOther : showOther
		});
	}

	// 填充学生成绩
	,fillStudentCourseGrade: function(options) {
		var contextPath = options.contextPath, //项目路径，固定值'${sessionScope.contextPath}'
			tagId = options.tagId, 	   			//填充id
			scgShow = options.scgShow;			//成绩数据
		var cnt = 0;
		$('#'+tagId).empty();
		if (null!=scgShow && 0<scgShow.length) {
			for (var i=0; i<scgShow.length; i++) {
				if (0 < scgShow[i].length) {
					var $eachSemester = $('<div style="margin-top:'+(0<cnt?5:0)+'px;"></div>');
					$eachSemester.append('<span style="font-size:20px;font-weight:bolder;display:block;margin-bottom:5px;">'+scgShow[i][0].semesterName+'</span>');
					for (var j=0; j<scgShow[i].length; j++) {
						if (j > 0) {
							$eachSemester.append('<span style="display:inline-block;margin-left:5px;margin-right:5px;">|</span>');
						}
						$eachSemester.append(scgShow[i][j].courseName+"（"+(60<=scgShow[i][j].grade?scgShow[i][j].grade+'分':'<span style="color:red;">'+(-1==scgShow[i][j].grade?'未录入':scgShow[i][j].grade+'分')+'</span>')+'）');
					}
					$eachSemester.appendTo($('#'+tagId));
					++cnt;
				}

			}
		}
	}

	// 渲染：给table-tr加删除线
	,addRemoveLineToTr: function(trNode) {
		$(trNode).find('td').each(function(index){
//			$(this).children().attr("disabled", "disabled").children().attr("disabled", "disabled");
            if (index == 0) {//重点部分
                var t = $(this).offset().top + $(this).height();//1、获得对应行，第一列相对于浏览器顶部的位移
                var l = $(this).offset().left;//2、获得对应行，第一列相对于浏览器左侧的位移
                var w = $(this).parent("tr").width();//3、获得对应行的宽度
                $(this).children("*:last").after("<div class='trRemoveLine' style='outline:red solid 3px; position:absolute; left:0px;top:" + (t-212) + "px;width:" + w + "px;z-index:9999;'></div>");//4
            }
		});
	}

	// 渲染：删除table-tr删除线
	,rmRemoveLineToTr: function(trNode) {
		$(trNode).find('.trRemoveLine').remove();
	}

	,compareNumber :function (val1, val2) {
		return val1-val2;
	}

	// dataTable单元格合并（竖向）
	,tdMergeVertical: function(options) {
		var tableTagId = options.tableTagId;
		var verticalIndex = options.verticalIndex;
		var verticalIndexSameLevel = options.verticalIndexSameLevel;
		var considerBefore = options.considerBefore?options.considerBefore:false;
		var considerAfter = options.considerAfter?options.considerAfter:false;
		var joinerFlag = '--+--';

		var verticalIdxs = [];
		verticalIdxs.push(verticalIndex);
		if (verticalIndexSameLevel) {
			for (var i=0; i<verticalIndexSameLevel.length; i++) {
				if (verticalIndexSameLevel[i]) {
					verticalIdxs.push(verticalIndexSameLevel[i]);
				}
			}
		}
		verticalIdxs.sort(this.compareNumber);

		// 合并
        var merger = [];
        var compareVal = '';
        var cnt = 0;
        $('#'+tableTagId+' tbody tr').each(function(index){
        	if (considerBefore) {
        		if (0!=index && compareVal!=(($(this).find('td:eq('+verticalIndex+')').html()+'').trim()+joinerFlag+($(this).find('td:eq('+(verticalIndex-1)+')').html()+'').trim())) {
            		compareVal = ($(this).find('td:eq('+verticalIndex+')').html()+'').trim()+joinerFlag+($(this).find('td:eq('+(verticalIndex-1)+')').html()+'').trim();
            		merger.push(cnt);
            		cnt = 1;
            	} else {
            		++cnt;
            		compareVal = ($(this).find('td:eq('+verticalIndex+')').html()+'').trim()+joinerFlag+($(this).find('td:eq('+(verticalIndex-1)+')').html()+'').trim();
            	}
        	} else if (considerAfter) {
        		if (0!=index && compareVal!=(($(this).find('td:eq('+verticalIndex+')').html()+'').trim()+joinerFlag+($(this).find('td:eq('+(verticalIndex+1)+')').html()+'').trim())) {
            		compareVal = ($(this).find('td:eq('+verticalIndex+')').html()+'').trim()+joinerFlag+($(this).find('td:eq('+(verticalIndex+1)+')').html()+'').trim();
            		merger.push(cnt);
            		cnt = 1;
            	} else {
            		++cnt;
            		compareVal = ($(this).find('td:eq('+verticalIndex+')').html()+'').trim()+joinerFlag+($(this).find('td:eq('+(verticalIndex+1)+')').html()+'').trim();
            	}
        	} else {
        		if (0!=index && compareVal!=($(this).find('td:eq('+verticalIndex+')').html()+'').trim()) {
            		compareVal = ($(this).find('td:eq('+verticalIndex+')').html()+'').trim();
            		merger.push(cnt);
            		cnt = 1;
            	} else {
            		++cnt;
            		compareVal = ($(this).find('td:eq('+verticalIndex+')').html()+'').trim();
            	}
        	}
        });
        if (0 < cnt) {
        	merger.push(cnt);
        }
        var trIdx = 0;
        for (var i=0; i<merger.length; i++) {
        	if (considerBefore) {
        		$('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+verticalIndex+')').attr('rowspan', merger[i]);
            	$('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+verticalIndex+')').css('vertical-align', 'middle');
            	$('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+verticalIndex+')').css('background-color', 'white');
            	$('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+(verticalIndex-1)+')').attr('rowspan', merger[i]);
            	$('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+(verticalIndex-1)+')').css('vertical-align', 'middle');
            	$('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+(verticalIndex-1)+')').css('background-color', 'white');
            	for (var j=1; j<merger[i]; j++) {
            		$('#'+tableTagId+' tbody tr:eq('+(trIdx+j)+') td:eq('+verticalIndex+')').remove();
            		$('#'+tableTagId+' tbody tr:eq('+(trIdx+j)+') td:eq('+(verticalIndex-1)+')').remove();
            	}
    		} else if (considerAfter) {
    			$('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+verticalIndex+')').attr('rowspan', merger[i]);
            	$('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+verticalIndex+')').css('vertical-align', 'middle');
            	$('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+verticalIndex+')').css('background-color', 'white');
            	$('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+(verticalIndex+1)+')').attr('rowspan', merger[i]);
            	$('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+(verticalIndex+1)+')').css('vertical-align', 'middle');
            	$('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+(verticalIndex+1)+')').css('background-color', 'white');
            	for (var j=1; j<merger[i]; j++) {
            		$('#'+tableTagId+' tbody tr:eq('+(trIdx+j)+') td:eq('+(verticalIndex+1)+')').remove();
            		$('#'+tableTagId+' tbody tr:eq('+(trIdx+j)+') td:eq('+verticalIndex+')').remove();
            	}
    		} else {
    			// $('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+verticalIndex+')').attr('rowspan', merger[i]);
            	// $('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+verticalIndex+')').css('vertical-align', 'middle');
            	// $('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+verticalIndex+')').css('background-color', 'white');
            	// for (var j=1; j<merger[i]; j++) {
            	// 	$('#'+tableTagId+' tbody tr:eq('+(trIdx+j)+') td:eq('+verticalIndex+')').remove();
            	// }
				for (var it=verticalIdxs.length-1; it>=0; it--) {
					$('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+verticalIdxs[it]+')').attr('rowspan', merger[i]);
					$('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+verticalIdxs[it]+')').css('vertical-align', 'middle');
					$('#'+tableTagId+' tbody tr:eq('+trIdx+') td:eq('+verticalIdxs[it]+')').css('background-color', 'white');
					for (var j=1; j<merger[i]; j++) {
						$('#'+tableTagId+' tbody tr:eq('+(trIdx+j)+') td:eq('+verticalIdxs[it]+')').remove();
					}
				}
    		}
        	trIdx = trIdx+merger[i];
        }
	}
	// dataTable单元格合并撤销（竖向）
	,tdMergeVerticalCallBack: function(options) {
		var tableTagId = options.tableTagId;
		var verticalIndex = options.verticalIndex;
		var totalTdLength = options.totalTdLength;
		var considerBefore = options.considerBefore?options.considerBefore:false;
		var considerAfter = options.considerAfter?options.considerAfter:false;

		$('#'+tableTagId+' tbody tr').each(function(index){
			var curTbLength = totalTdLength-$(this).find('td').length;
			for (var it=0; it<curTbLength; it++) {
				if (0==verticalIndex) {
					$(this).find('td:eq(0)').before('<td></td>');
				} else {
					if (considerBefore && 2==curTbLength && 0==(verticalIndex-1)) {
						$(this).find('td:eq('+(verticalIndex-1)+')').before('<td></td>');
					} else {
						$(this).find('td:eq('+(verticalIndex-1)+')').after('<td></td>');
					}
				}
			}
		});
	}
	// 格式化日期控件
	,formatDate: function(options) {
		$('.form_date').each(function () {
           var params = {};
           params['language'] = 'zh-CN';
           params['weekStart'] = 1;
           params['autoclose'] = 1;
           params['todayHighlight'] = true;
           params['keyboardNavigation'] = true;
           params['todayBtn'] = true;
           params['forceParse'] = true;

           var eachTagClass = $(this).attr('class').split(' ');
           for (var i = 0; i < eachTagClass.length; i++) {
               if ('fyear' == eachTagClass[i].trim()) {
                   params['format'] = 'yyyy';
                   params['startView'] = 4;
                   params['minView'] = 4;
               } else if ('fmonth' == eachTagClass[i].trim()) {
                   params['format'] = 'yyyy-mm';
                   params['startView'] = 3;
                   params['minView'] = 3;
               } else if ('fmonth-point' == eachTagClass[i].trim()) {
                   params['format'] = 'yyyy.mm';
                   params['startView'] = 3;
                   params['minView'] = 3;
               } else if ('fday' == eachTagClass[i].trim()) {
                   params['format'] = 'yyyy-mm-dd';
                   params['startView'] = 2;
                   params['minView'] = 2;
               }
           }

           $(this).datetimepicker(params);
        });
	}
	,divDraggable: function(options){
		var divNode = options.divNode;	//div对象
		var draggalbe = options.draggalbe||false; //是否可拖动
		var resize = options.resize||false;	//是否可拖动大小（暂未实现）
		var xLeft = options.xLeft||0;	//偏移量
		var fixWhenFocus = options.fixWhenFocus||true;	//光标在input标签内是否可拖动

		if (divNode) {
			if (draggalbe) {//支持窗口拖动
				var fnlX;
				var fnlY;
				$(divNode).mousedown(function(e){
					if (!fixWhenFocus || (fixWhenFocus && 0==$(':focus').length)) {
						$(this).css("cursor","move");//改变鼠标指针的形状
			            var offset = $(this).offset();//DIV在页面的位置
			            var x = e.pageX - offset.left;//获得鼠标指针离DIV元素左边界的距离
			            var y = e.pageY - offset.top;//获得鼠标指针离DIV元素上边界的距离
			            $(document).bind("mousemove",function(ev){ //绑定鼠标的移动事件，因为光标在DIV元素外面也要有效果，所以要用doucment的事件，而不用DIV元素的事件
			                $(divNode).stop();//加上这个之后
			                var _y_scroll_top = $(document).scrollTop()||0;
			                var _x = ev.pageX - x + xLeft;//获得X轴方向移动的值
			                var _y = ev.pageY - y - _y_scroll_top;//获得Y轴方向移动的值
			                fnlX = ev.pageX;
			                fnlY = ev.pageY;
			                $(divNode).animate({left:_x+"px",top:_y+"px"},10);
			            });
					}
				});
				$(document).mouseup(function(e){
					$(divNode).css("cursor","default");
		            $(this).unbind("mousemove");
				});
			}
			if (resize) {//支持改变窗口大小

			}
		}
	},
	printAPP:function(options){
		$("#"+options.ele).print({
			globalStyles:true,//是否包含父文档的样式，默认为true
			mediaPrint:false,//是否包含media='print'的链接标签。会被globalStyles选项覆盖，默认为false
			stylesheet:'',//外部样式表的URL地址，默认为null
			noPrintSelector:".no-print",//不想打印的元素的jQuery选择器，默认为".no-print"
			iframe:true,//是否使用一个iframe来替代打印表单的弹出窗口，true为在本页面进行打印，false就是说新开一个页面打印，默认为true
			append:null,//将内容添加到打印内容的后面
			prepend:null//将内容添加到打印内容的前面，可以用来作为要打印内容
		});
	}
	,isIE:function(){
		if (!!window.ActiveXObject || "ActiveXObject" in window) {
        	return true;
        } else {
        	return false;
        }
	}
	// 分页打印工具类
	,printTbl:function (optins) {
		var layout = optins.layout||'Portrait';// 打印方向：Portrait|Landscape
		var fixedHeight = optins.fixedHeight;// 每页打印表格tbody最大高度，超过分页
		var defaultPortraitHeight = 950;// 纵向打印默认分页高度
		var defaultLandscapeHeight = 650;// 纵向打印默认分页高度
		var eachPartEmptyHtml = optins.eachPartEmptyHtml;// 分页初始标签
		if (null == fixedHeight) {
			fixedHeight = ('Portrait'==layout?defaultPortraitHeight:defaultLandscapeHeight);
		}

		$('#printFld1').empty();
		$('#printFld1').css('display', '');
		$('#printFld').css('display', '');
		var trIdx = [];
		trIdx.push(0);
		var heightArray = [];
		var trArray = [];
		var totalHeight = 0;
		$('#printTbl tbody tr').each(function(){
			heightArray.push(parseInt(($(this).css('height')+'').replace('px','')));
			var $copyTr = $('<tr></tr>');
			$copyTr.html($(this).html());
			trArray.push($copyTr);
		});
		var compareHeight = fixedHeight;
		if ($.isIE()) {
			compareHeight = fixedHeight;
		}
		for (var i=0; i<heightArray.length; i++) {
			totalHeight += heightArray[i];
			if (compareHeight < totalHeight) {
				totalHeight = heightArray[i];
				trIdx.push(i);
			}
		}
		for (var j=0; j<trIdx.length; j++) {
			if (0 == j) {
				if ($.isIE()) {
					$('#printFld1').append('<div style="page-break-after:always;"></div><div style="margin-top:30px;">&nbsp;</div>'+eachPartEmptyHtml);
				} else {
					$('#printFld1').append(eachPartEmptyHtml);
				}
			} else {
				if ($.isIE()) {
					$('#printFld1').append('<div style="page-break-after:always;"></div><div style="margin-top:30px;">&nbsp;</div>'+eachPartEmptyHtml);
				} else {
					$('#printFld1').append('<div style="page-break-after:always;"></div>'+eachPartEmptyHtml);
				}
			}
		}

		setTimeout(function(){
			$('#printFld').css('display', 'none');
			for (var j=0; j<trIdx.length; j++) {
				if (j < trIdx.length-1) {
					for (var k=trIdx[j]; k<trIdx[j+1]; k++) {
						$('#printFld1').find('table:eq('+j+') tbody').append(trArray[k]);
					}
				} else {
					for (var k=trIdx[j]; k<trArray.length; k++) {
						$('#printFld1').find('table:eq('+j+') tbody').append(trArray[k]);
					}
				}
			}

			setTimeout(function(){
				$("#printFld1").print({
					globalStyles:true,//是否包含父文档的样式，默认为true
					mediaPrint:false,//是否包含media='print'的链接标签。会被globalStyles选项覆盖，默认为false
					stylesheet:'',//外部样式表的URL地址，默认为null

					noPrintSelector:".no-print",//不想打印的元素的jQuery选择器，默认为".no-print"
					iframe:true,//是否使用一个iframe来替代打印表单的弹出窗口，true为在本页面进行打印，false就是说新开一个页面打印，默认为true
					append:null,//将内容添加到打印内容的后面
					prepend:null,//将内容添加到打印内容的前面，可以用来作为要打印内容
					deferred:
						$.Deferred(function(){
							setTimeout(function(){
								$("#printFld1").css("display","none");
								$("#printFld").css("display","none");
							}, 500);
						})//回调函数
				});
			}, 200);
		}, 500);
	}
	// 查询所有教学楼，填充到select标签
	,getAllBuildings: function(options) {
		var contextPath = options.contextPath; //项目根路径
		var tagId = options.tagId; //select标签id
		var appendEmptyOpt = options.appendEmptyOpt;	//是否添加空选项
		var emptyOptPosition = options.emptyOptPosition;	//空选项位置
		var orgBuildingName = options.orgBuildingName;//回显值
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var asyncType = (options.asyncType?options.asyncType:false);
		$.ajax({
			url:contextPath+'/common/buildings',
			type:'POST',
			dataType:'json',
			data: {'ordered':true, 'sortType':'asc'},
			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();
				if (appendEmptyOpt && 'top' == emptyOptPosition) {
					$('#'+tagId).append('<option value=""></option>');
				}
				if (result.success && result.buildings && 0<result.buildings.length)
				{
					for (var i=0; i<result.buildings.length; i++) {
						if (null==orgBuildingName || ''==orgBuildingName) {
							$('#'+tagId).append('<option value="'+result.buildings[i].ID +'">' + result.buildings[i].NAME + '</option>');
						} else {
							$('#'+tagId).append('<option value="'+result.buildings[i].ID+'"'+(orgBuildingName==result.buildings[i].NAME?'selected':'')+'>'+result.buildings[i].NAME+'</option>');
						}
					}
				}
				if (appendEmptyOpt && 'tail' == emptyOptPosition) {
					$('#'+tagId).append('<option value=""></option>');
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
					$('#'+tagId).chosen('destroy');
					$('#'+tagId+'_chzn').remove();
					$('#'+tagId).removeClass('chzn-done');
					$('#'+tagId).attr('data-placeholder', ' ');
					$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
				}
			},
			error:function(msg){

			}
		});
	}
	// 查询所有教室，填充到select标签
	,getAllClassrooms: function(options) {
		var contextPath = options.contextPath; //项目根路径
		var tagId = options.tagId; //select标签id
		var orgRoomCode = options.orgRoomCode;//回显值
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var asyncType = (options.asyncType?options.asyncType:false);
		$.ajax({
			url:contextPath+'/common/classroomSS',
			type:'POST',
			dataType:'json',
			data: {'ordered':true, 'sortType':'asc'},
			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();
				//$('#'+tagId).append('<option value="">　</option>');
				if (result.success && result.classroomSS && 0<result.classroomSS.length)
				{
					for (var i=0; i<result.classroomSS.length; i++) {
						if (null==orgRoomCode || ''==orgRoomCode) {
							$('#'+tagId).append('<option value="'+result.classroomSS[i].jsh +'">' + result.classroomSS[i].jsh + '</option>');
						} else {
							$('#'+tagId).append('<option value="'+result.classroomSS[i].jsh+'"'+(orgRoomCode==result.classroomSS[i].jsh?'selected':'')+'>'+result.classroomSS[i].jsh+'</option>');
						}
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
					$('#'+tagId).chosen('destroy');
					$('#'+tagId+'_chzn').remove();
					$('#'+tagId).removeClass('chzn-done');
					$('#'+tagId).attr('data-placeholder', ' ');
					$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
				}
			},
			error:function(msg){

			}
		});
	}
	// 查询所有教室（特殊：包括排课表中存在的教室），填充到select标签
	,getAllClassroomsSp: function(options) {
		var contextPath = options.contextPath; //项目根路径
		var tagId = options.tagId; //select标签id
		var orgRoomCode = options.orgRoomCode;//回显值
		var buildingId = options.buildingId;//教学楼id
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var asyncType = (options.asyncType?options.asyncType:false);
		$.ajax({
			url:contextPath+'/common/classroomSSSp',
			type:'POST',
			dataType:'json',
			data: {'ordered':true, 'sortType':'asc', 'buildingId':buildingId},
			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();
				//$('#'+tagId).append('<option value="">　</option>');
				if (result.success && result.classroomSS && 0<result.classroomSS.length)
				{
					for (var i=0; i<result.classroomSS.length; i++) {
						if (null==orgRoomCode || ''==orgRoomCode) {
							$('#'+tagId).append('<option value="'+result.classroomSS[i].JS +'">' + result.classroomSS[i].JS + '</option>');
						} else {
							$('#'+tagId).append('<option value="'+result.classroomSS[i].JS+'"'+(orgRoomCode==result.classroomSS[i].JS?'selected':'')+'>'+result.classroomSS[i].JS+'</option>');
						}
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
					$('#'+tagId).chosen('destroy');
					$('#'+tagId+'_chzn').remove();
					$('#'+tagId).removeClass('chzn-done');
					$('#'+tagId).attr('data-placeholder', ' ');
					$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
				}
			},
			error:function(msg){

			}
		});
	}
	// dataTable fnDrawCallback调用本方法处理：最后一页只有一条数据，删除之后自动跳转到前一页码，避免留在当前空数据页码，且左下角表格数据量溢出
	,goPrePage: function (options) {
		var tblTag = options.tblTag;
		var tblWrapTag = options.tblWrapTag?options.tblWrapTag:(tblTag+'_wrapper');

		var tblSettings = $('#'+tblTag).dataTable().fnSettings();
		var displayStart = tblSettings._iDisplayStart;
		var displayLength = tblSettings._iDisplayLength;
		setTimeout(function(){
			if (0 < displayStart && 0 < $('#'+tblTag+' tbody td.dataTables_empty').length) {
				displayStart = displayStart - displayLength;
				$('#'+tblTag).dataTable().fnPageChange(displayStart/displayLength);
			}
		}, 100);
	}
	// add by lijie 20190429 学生查询成绩前判断评教/毕业问卷调查是否填写统一入口
	,studentEvalAndQuestionnaire: function (options) {
		var contextPath = options.contextPath; //项目根路径
		var forwardUrl = options.forwardUrl; //跳转到成绩查询页面
		var isSelectCourse = options.isSelectCourse?options.isSelectCourse:false; //是否选课操作
		$.ajax({
			type:'post',
			url:contextPath+'/grade/querygrade/istestNew',
			data:{isSelectCourse:isSelectCourse},
			success:function(data){
				if(data.success){
					window.location.href = forwardUrl;
				}else{
					window.location.href = contextPath+data.writePage;
				}
			}

		})
	}

	/** add by xtL 20190618 begin **/
	// 按照学生查询该生所在专业上一年级的所有班级，填充到select标签
	,getBeforeClassesInMajorByXh: function(options) {
		var contextPath = options.contextPath; //项目根路径
		var tagId = options.tagId; //select标签id
		var studentNo = options.studentNo;//学号
		var ordered = (null==options.ordered?true:options.ordered);//是否排序，默认排序
		var sortType = (this.stringIsEmpty(options.sortType)?'desc':options.sortType);//排序类型，默认降序
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var asyncType = (options.asyncType?options.asyncType:false);
		$.ajax({
			url:contextPath+'/common/majorBeforeClassSS',
			type:'POST',
			dataType:'json',
			data: {'ordered':ordered, 'sortType':sortType, 'studentNo':studentNo},
			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();
				$('#'+tagId).append('<option value="">　</option>');
				if (result.success && result.majorBeforeClassSS && 0<result.majorBeforeClassSS.length)
				{
					for (var i=0; i<result.majorBeforeClassSS.length; i++) {
						$('#'+tagId).append('<option value="'+result.majorBeforeClassSS[i].id+'">'+result.majorBeforeClassSS[i].name+'</option>');
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
					$('#'+tagId).chosen('destroy');
					$('#'+tagId+'_chzn').remove();
					$('#'+tagId).removeClass('chzn-done');
					$('#'+tagId).attr('data-placeholder', ' ');
					$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
				}
			},
			error:function(msg){

			}
		});
	}
	,showLoading: function (options) {
		var contextPath = options.contextPath;
		var loadStyle = 'width:160px;height:56px;position: fixed;top:50%;left:50%;line-height:56px;color:#fff;padding-left:60px;font-size:15px;background: #000 url('+contextPath+'/images/icon/load.gif) no-repeat 10px 50%;opacity: 0.7;z-index:9999;-moz-border-radius:20px;-webkit-border-radius:20px;border-radius:20px;filter:progid:DXImageTransform.Microsoft.Alpha(opacity=70);';
		if (0 == $('#loadingFld').length) {
			$('body').append('<div class="modal fade" id="loadingFld" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" data-backdrop="static" style="border:0px solid white;">\n' +
									'<div class="modal-dialog" role="document">\n' +
										'<div style="'+loadStyle+'" >请稍等...</div>\n' +
									'</div>\n' +
								'</div>');
		}
		setTimeout(function () {
			$('#loadingFld').modal('show');
		}, 10);
	}
	,hideLoading: function () {
		$('#loadingFld').modal('hide');
	}
	,getYear: function () {
		var year = new Date().getFullYear();
		return year;
	}
	,getMonth: function (type) {
		var month = new Date().getMonth()+1;
		if (1==type) {
			if (1 == (month+'').length) {
				month = '0'+month
			}
		}
		return month;
	}
	,getDay: function (type) {
		var day = new Date().getDate();
		if (1==type) {
			if (1 == (day+'').length) {
				day = '0'+day
			}
		}
		return day;
	}
	,appendEmptySpace: function () {
		return '　';
	}
	/** add by xtL 20190618 end **/
	//获取主键为组织机构编号的数据
	,getAllOrgnizationsOfCode: function(options) {
		var contextPath = options.contextPath; //项目根路径
		var tagId = options.tagId; //select标签id
		var orgOrgnId = options.orgOrgnId;//回显值
		var chosenFormat = options.chosenFormat;//是否格式化chosen
		var orgnType = options.orgnType;//是否格式化chosen
		var asyncType = (options.asyncType?options.asyncType:false);
		var isAcademy=(options.isAcademy==true?1:0);
		var autoWidth = (null!=options.autoWidth?options.autoWidth:false);//下拉框自适应宽度（一个字符15px）
		var ordered = (null!=options.ordered?options.ordered:true);
		var isMulti = options.isMulti; 				//是否多选
		var fixedOrgn = options.fixedOrgn||null;
		var appointScope = options.appointScope||null;
		var appendEmptyOpt = (null!=options.appendEmptyOpt?options.appendEmptyOpt:true);	//是否添加空选项
		var maxWidthLen = 0;
		$.ajax({
			url:contextPath+'/common/orgnSSOfCode',
			type:'POST',
			dataType:'json',
			data: {'ordered':ordered, 'sortType':'asc', 'orgnType':orgnType,'isAcademy':isAcademy},
			async: asyncType,
			success:function(result){
				$('#'+tagId).empty();
				if (appendEmptyOpt) {
					$('#'+tagId).append('<option value="">　</option>');
				}
				if (result.success && result.orgnSS && 0<result.orgnSS.length)
				{
					if (appointScope) {
						appointScope = ','+appointScope+',';
						for (var i=0; i<result.orgnSS.length; i++) {
							if (-1 == appointScope.indexOf(','+result.orgnSS[i].id+',')) {
								continue;
							}
							if (null!=fixedOrgn && fixedOrgn!=result.orgnSS[i].id) {
								continue;
							}
							var curOptLen = $.getChineseCharLen(result.orgnSS[i].name);
							if (maxWidthLen < curOptLen) {
								maxWidthLen = curOptLen;
							}
							if (null==orgOrgnId || ''==orgOrgnId) {
								$('#'+tagId).append('<option value="'+result.orgnSS[i].id+'">'+result.orgnSS[i].name+'</option>');
							} else {
								$('#'+tagId).append('<option value="'+result.orgnSS[i].id+'" '+(orgOrgnId==result.orgnSS[i].id?'selected':'')+'>'+result.orgnSS[i].name+'</option>');
							}
						}
					} else {
						for (var i=0; i<result.orgnSS.length; i++) {
							if (null!=fixedOrgn && fixedOrgn!=result.orgnSS[i].id) {
								continue;
							}
							var curOptLen = $.getChineseCharLen(result.orgnSS[i].name);
							if (maxWidthLen < curOptLen) {
								maxWidthLen = curOptLen;
							}
							if (null==orgOrgnId || ''==orgOrgnId) {
								$('#'+tagId).append('<option value="'+result.orgnSS[i].id+'">'+result.orgnSS[i].name+'</option>');
							} else {
								$('#'+tagId).append('<option value="'+result.orgnSS[i].id+'" '+(orgOrgnId==result.orgnSS[i].id?'selected':'')+'>'+result.orgnSS[i].name+'</option>');
							}
						}
					}
				}

				if (chosenFormat && 0<$('#'+tagId+' option').length) {
					$('#'+tagId).chosen('destroy');
					$('#'+tagId+'_chzn').remove();
					$('#'+tagId).removeClass('chzn-done');
					$('#'+tagId).attr('data-placeholder', ' ');
					$('#'+tagId).chosen({no_results_text:'没有结果匹配'});
					if (autoWidth) {
						if ($.chosenDropDefaultWidth() < (maxWidthLen*15/2+50)) {
							$('#'+tagId+'_chzn .chzn-drop').css('width', (maxWidthLen*15/2+50)+'px');
						}
					}
				}
			},
			error:function(msg){

			}
		});
	}
});

//字符数组包含
Array.prototype.contains = function(item){
    return RegExp(item).test(this);
};
//字符数组精确包含
Array.prototype.containsPrecise = function(item){
    var len = this.length;
	while (len--) {
		if (item == this[len])
			return true;
	}
    return false;
};
//对象数组成员变量包含
Array.prototype.containFieldVal = function(field, value){
	var len = this.length;
	while (len--) {
		if (RegExp(value).test(this[len][field]))
			return true;
	}
    return false;
};
//对象数组成员变量精确包含
Array.prototype.containFieldValPrecise = function(field, value){
	var len = this.length;
	while (len--) {
		if (value == this[len][field])
			return true;
	}
	return false;
};
//对象数组成员变量精确包含
Array.prototype.containField2ValPrecise = function(field1, field2, value1, value2){
	var len = this.length;
	while (len--) {
		if (value1==this[len][field1] && value2==this[len][field2])
			return true;
	}
	return false;
};
Date.prototype.Format = function (fmt) { //author: meizz
    var o = {
        "M+": this.getMonth() + 1, //月份
        "d+": this.getDate(), //日
        "H+": this.getHours(), //小时
        "m+": this.getMinutes(), //分
        "s+": this.getSeconds(), //秒
        "q+": Math.floor((this.getMonth() + 3) / 3), //季度
        "S": this.getMilliseconds() //毫秒
    };
    if (/(y+)/.test(fmt)) fmt = fmt.replace(RegExp.$1, (this.getFullYear() + "").substr(4 - RegExp.$1.length));
    for (var k in o)
    if (new RegExp("(" + k + ")").test(fmt)) fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (("00" + o[k]).substr(("" + o[k]).length)));
    return fmt;
};

function getContextPath() {
	var pathName = document.location.pathname;
	var index = pathName.substr(1).indexOf("/");
	var result = pathName.substr(0,index+1);
	return result;
}

function getLoginReload() {
	$.ajax({
		url:getContextPath()+'/getlr',
		type:'GET',
		dataType:'json',
		data:{},
		success:function(result){
			if (result.success && 1==result.loginReload) {
				invalidLoginReload();
				setTimeout(function () {
                    $('li.start.open ul:eq(0) li:eq(0) a').trigger('click');
                }, 100);
			}
		},
		error:function(){

		}
	});
}
function invalidLoginReload() {
	$.ajax({
		url:getContextPath()+'/invalidlr',
		type:'GET',
		dataType:'json',
		data:{},
        async:false,
		success:function(result){
			if (result.success) {
			}
		},
		error:function(){

		}
	});
}
// getLoginReload();