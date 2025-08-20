package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strconv"
	"time"

	"github.com/weaviate/weaviate-go-client/v4/weaviate"
	"github.com/weaviate/weaviate-go-client/v4/weaviate/auth"
	"github.com/weaviate/weaviate-go-client/v4/weaviate/filters"
	"github.com/weaviate/weaviate-go-client/v4/weaviate/graphql"
	"github.com/weaviate/weaviate/entities/models"
)

type WeaviateConnection struct {
	client *weaviate.Client
}

func NewWeaviateConnection() (*WeaviateConnection, error) {
	host := getEnvWithDefault("WEAVIATE_HOST", "localhost:8080")
	scheme := getEnvWithDefault("WEAVIATE_SCHEME", "http")
	apiKey := getEnvWithDefault("WEAVIATE_API_KEY", "")
	timeoutStr := getEnvWithDefault("WEAVIATE_STARTUP_TIMEOUT", "1")
	
	timeout, err := strconv.Atoi(timeoutStr)
	if err != nil {
		return nil, fmt.Errorf("invalid WEAVIATE_STARTUP_TIMEOUT: %w", err)
	}
	
	config := weaviate.Config{
		Host:           host,
		Scheme:         scheme,
		StartupTimeout: time.Duration(timeout) * time.Second,
	}
	
	if apiKey != "" {
		config.AuthConfig = auth.ApiKey{Value: apiKey}
	}
	
	client, err := weaviate.NewClient(config)
	if err != nil {
		return nil, fmt.Errorf("connect to weaviate: %w", err)
	}
	return &WeaviateConnection{client}, nil
}

func (conn *WeaviateConnection) InsertOne(ctx context.Context,
	collection string, props interface{},
) (*models.Object, error) {
	obj := models.Object{
		Class:      collection,
		Properties: props,
	}
	// Use batch to leverage autoschema and gRPC
	resp, err := conn.batchInsert(ctx, &obj)
	if err != nil {
		return nil, fmt.Errorf("insert one object: %w", err)
	}

	return &resp[0].Object, err
}

func (conn *WeaviateConnection) Query(ctx context.Context, collection,
	query string, targetProps []string, whereFilter map[string]interface{}, limit *int, offset *int,
) (string, error) {
	hybrid := graphql.HybridArgumentBuilder{}
	hybrid.WithQuery(query)
	
	queryBuilder := conn.client.GraphQL().Get().
		WithClassName(collection).WithHybrid(&hybrid).
		WithFields(func() []graphql.Field {
			fields := make([]graphql.Field, len(targetProps))
			for i, prop := range targetProps {
				fields[i] = graphql.Field{Name: prop}
			}
			return fields
		}()...)
	
	// Add filter if provided
	if whereFilter != nil {
		filter, err := conn.buildWhereFilter(whereFilter)
		if err != nil {
			return "", fmt.Errorf("build where filter: %w", err)
		}
		queryBuilder = queryBuilder.WithWhere(filter)
	}
	
	// Add limit if provided
	if limit != nil {
		queryBuilder = queryBuilder.WithLimit(*limit)
	}
	
	// Add offset if provided
	if offset != nil {
		queryBuilder = queryBuilder.WithOffset(*offset)
	}
	
	res, err := queryBuilder.Do(context.Background())
	if err != nil {
		return "", err
	}
	b, err := json.Marshal(res)
	if err != nil {
		return "", fmt.Errorf("unmarshal query response: %w", err)
	}
	return string(b), nil
}

func (conn *WeaviateConnection) batchInsert(ctx context.Context, objs ...*models.Object) ([]models.ObjectsGetResponse, error) {
	resp, err := conn.client.Batch().ObjectsBatcher().WithObjects(objs...).Do(ctx)
	if err != nil {
		return nil, fmt.Errorf("make insertion request: %w", err)
	}
	for _, res := range resp {
		if res.Result != nil && res.Result.Errors != nil && res.Result.Errors.Error != nil {
			for _, nestedErr := range res.Result.Errors.Error {
				err = errors.Join(err, errors.New(nestedErr.Message))
			}
		}
	}

	return resp, err
}

func (conn *WeaviateConnection) buildWhereFilter(filterMap map[string]interface{}) (*filters.WhereBuilder, error) {
	operator, ok := filterMap["operator"].(string)
	if !ok {
		return nil, fmt.Errorf("filter must have an 'operator' field")
	}

	where := filters.Where()

	switch operator {
	case "And":
		operands, ok := filterMap["operands"].([]interface{})
		if !ok {
			return nil, fmt.Errorf("And operator requires 'operands' array")
		}
		
		var subFilters []*filters.WhereBuilder
		for _, operand := range operands {
			operandMap, ok := operand.(map[string]interface{})
			if !ok {
				return nil, fmt.Errorf("each operand must be an object")
			}
			subFilter, err := conn.buildWhereFilter(operandMap)
			if err != nil {
				return nil, fmt.Errorf("build sub-filter: %w", err)
			}
			subFilters = append(subFilters, subFilter)
		}
		where.WithOperator(filters.And).WithOperands(subFilters)

	case "Or":
		operands, ok := filterMap["operands"].([]interface{})
		if !ok {
			return nil, fmt.Errorf("Or operator requires 'operands' array")
		}
		
		var subFilters []*filters.WhereBuilder
		for _, operand := range operands {
			operandMap, ok := operand.(map[string]interface{})
			if !ok {
				return nil, fmt.Errorf("each operand must be an object")
			}
			subFilter, err := conn.buildWhereFilter(operandMap)
			if err != nil {
				return nil, fmt.Errorf("build sub-filter: %w", err)
			}
			subFilters = append(subFilters, subFilter)
		}
		where.WithOperator(filters.Or).WithOperands(subFilters)

	default:
		// Single condition operators
		path, ok := filterMap["path"].([]interface{})
		if !ok {
			return nil, fmt.Errorf("filter must have a 'path' field")
		}
		
		var pathStrings []string
		for _, p := range path {
			pathStr, ok := p.(string)
			if !ok {
				return nil, fmt.Errorf("path elements must be strings")
			}
			pathStrings = append(pathStrings, pathStr)
		}

		where.WithPath(pathStrings)

		switch operator {
		case "Equal":
			where.WithOperator(filters.Equal)
		case "NotEqual":
			where.WithOperator(filters.NotEqual)
		case "LessThan":
			where.WithOperator(filters.LessThan)
		case "LessThanEqual":
			where.WithOperator(filters.LessThanEqual)
		case "GreaterThan":
			where.WithOperator(filters.GreaterThan)
		case "GreaterThanEqual":
			where.WithOperator(filters.GreaterThanEqual)
		case "Like":
			where.WithOperator(filters.Like)
		default:
			return nil, fmt.Errorf("unsupported operator: %s", operator)
		}

		// Set value based on type
		if val, ok := filterMap["valueText"]; ok {
			where.WithValueString(val.(string))
		} else if val, ok := filterMap["valueInt"]; ok {
			if intVal, ok := val.(float64); ok {
				where.WithValueInt(int64(intVal))
			} else if intVal, ok := val.(int); ok {
				where.WithValueInt(int64(intVal))
			} else {
				return nil, fmt.Errorf("valueInt must be a number")
			}
		} else if val, ok := filterMap["valueNumber"]; ok {
			if numVal, ok := val.(float64); ok {
				where.WithValueNumber(numVal)
			} else {
				return nil, fmt.Errorf("valueNumber must be a number")
			}
		} else if val, ok := filterMap["valueBoolean"]; ok {
			if boolVal, ok := val.(bool); ok {
				where.WithValueBoolean(boolVal)
			} else {
				return nil, fmt.Errorf("valueBoolean must be a boolean")
			}
		} else if val, ok := filterMap["valueDate"]; ok {
			where.WithValueString(val.(string))
		} else {
			return nil, fmt.Errorf("filter must have a value field (valueText, valueInt, valueNumber, valueBoolean, or valueDate)")
		}
	}

	return where, nil
}
